# Test Scenarios — SSE Coexistence Testing

The `test_traffic.py` harness exercises each scenario below against a
deployed test client. Each scenario maps to one or more `TestResult`
rows in the output.

## 1. HTTP traffic is allowed

- **Objective**: Confirm that traffic on TCP/80 reaches Apache on the test client from a public source.
- **Probe**: `http_reachable(host)` — a GET against `http://<host>/`.
- **Expected outcome**: HTTP 200; the default Apache welcome page is returned.

## 2. SSH is open only to allowlisted CIDRs

- **Objective**: Confirm that SSH on TCP/22 is open from the operator's IP (which should be in `ssh_cidr_blocks` per `terraform.tfvars`).
- **Probe**: `ssh_reachable(host)` — a non-authenticating TCP connect to port 22.
- **Expected outcome**: `port open` when the running host is in the allowlist; `port filtered` otherwise.

## 3. Unsolicited ports are closed

- **Objective**: Confirm UFW's default-deny behaves as expected — no unintended services exposed.
- **Probe**: `other_ports_closed(host, ports=(23, 3389, 8080))` — TCP connect attempts to a sampling of typical-attack-surface ports.
- **Expected outcome**: all probed ports report `closed`.

## Limitations

- The harness can only probe from the machine it runs on. To prove source-IP filtering on SSH, run the harness from an IP that is *not* in `ssh_cidr_blocks` and confirm `ssh/22 reachable` flips to FAIL — this is the manual step the README's "validation walkthrough" calls for.
- These are reachability tests, not authentication tests. A real pen-test would add credential / vulnerability probes; that is intentionally out of scope.
