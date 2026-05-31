#requires -Version 5.1
# fix_encodings.ps1 -- find source files saved as UTF-16 and re-save them as
# UTF-8 (no BOM). UTF-16 requirements.txt / .py break pip and CI.
#
# DRY-RUN by default (lists what it WOULD change). Add -Apply to write.
#   .\fix_encodings.ps1            # preview
#   .\fix_encodings.ps1 -Apply     # fix
#
# Safe: only rewrites files whose bytes show a UTF-16 BOM or null bytes.
# UTF-8 files are left byte-for-byte untouched.

param([switch]$Apply)

$exts = '*.txt','*.py','*.toml','*.yml','*.yaml','*.json','*.md','*.rs','*.cfg','*.ini'
$skip = '\\\.git\\', '\\\.venv\\', '\\venv\\', '\\node_modules\\', '\\target\\'
$root = $PSScriptRoot
if (-not $root) { $root = (Get-Location).Path }

$changed = 0; $scanned = 0
foreach ($pattern in $exts) {
    Get-ChildItem -Path $root -Recurse -Filter $pattern -File -ErrorAction SilentlyContinue | ForEach-Object {
        $full = $_.FullName
        foreach ($s in $skip) { if ($full -match $s) { return } }
        $scanned++
        $bytes = [System.IO.File]::ReadAllBytes($full)
        if ($bytes.Length -lt 2) { return }

        $isUtf16 = $false; $enc = $null
        if ($bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) { $isUtf16 = $true; $enc = [System.Text.Encoding]::Unicode }       # UTF-16 LE BOM
        elseif ($bytes[0] -eq 0xFE -and $bytes[1] -eq 0xFF) { $isUtf16 = $true; $enc = [System.Text.Encoding]::BigEndianUnicode } # UTF-16 BE BOM
        else {
            # No BOM: detect by null bytes in the first 200 bytes (UTF-16 of ASCII text).
            $n = [Math]::Min(200, $bytes.Length)
            for ($i = 0; $i -lt $n; $i++) { if ($bytes[$i] -eq 0) { $isUtf16 = $true; $enc = [System.Text.Encoding]::Unicode; break } }
        }
        if (-not $isUtf16) { return }

        $changed++
        $rel = $full.Substring($root.Length).TrimStart('\')
        if ($Apply) {
            $text = $enc.GetString($bytes)
            if ($text.Length -gt 0 -and $text[0] -eq [char]0xFEFF) { $text = $text.Substring(1) }  # strip BOM char
            $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
            [System.IO.File]::WriteAllText($full, $text, $utf8NoBom)
            Write-Host "  fixed (UTF-16 -> UTF-8): $rel" -ForegroundColor Green
        } else {
            Write-Host "  WOULD FIX (UTF-16): $rel" -ForegroundColor Yellow
        }
    }
}
$verb = if ($Apply) { 'fixed' } else { 'would fix' }
Write-Host ""
Write-Host "Scanned $scanned source files; $verb $changed UTF-16 file(s).$(if (-not $Apply) {'  (dry-run -- add -Apply to write)'})" -ForegroundColor Cyan
