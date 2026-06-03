# Security Policy

This is a portfolio repository. Every project is labeled as a **simulation** or a **prototype**, not a production system. None of the code here should be deployed into an environment that handles real money, real votes, real customer data, or real network traffic — the blockchain, ML, and RAG projects each have a **Scope** section that spells out what they don't defend against.

A few concerns are real enough to merit a written policy.

## Reporting a vulnerability

If you find a security issue in any project in this repository, please report it privately first:

1. **Do not open a public GitHub issue.**
2. **Email**: [lmdixon23@gmail.com](mailto:lmdixon23@gmail.com) with the subject line `SECURITY: <project name>`.
3. **Include**:
    - The project / file path affected.
    - A description of the issue and its impact (what an attacker could do).
    - A minimal reproduction or proof of concept if you have one.
    - Whether you'd like to be credited in the fix.

I'll acknowledge receipt within 7 days and aim to publish a fix or a written response within 30 days. If the issue is in a third-party dependency rather than my code, I'll let you know and link to the upstream report when appropriate.

## What counts as in-scope

| Category | In scope | Out of scope |
|---|---|---|
| Code in this repository | ✅ everything under `ai_engineering/`, `machine_learning/`, `blockchain_protocols/`, `data_engineering/`, `network_security/`, `prototypes/` | n/a |
| Documentation | ✅ if an example in a README leaks credentials or recommends a clearly unsafe pattern | typos, formatting nits |
| Third-party dependencies | ⚠ I'll forward to upstream; no bounty | known issues already tracked by the upstream project |
| The author's personal infrastructure | n/a | ❌ not in scope |

## What is *not* a vulnerability in this repo

These are explicitly out of scope because every project README discloses them in its **Scope** section. Reporting them is fine, but they aren't bugs.

- The blockchain simulations are not real blockchains — no consensus, no real signatures over real chain state, no economic security. Anything that follows from "this is a single-process simulation" is not a vulnerability.
- The `network_security/sse_coexistence_testing/` Terraform module opens HTTP/80 to `0.0.0.0/0` by default in `terraform.tfvars.example`. That's intentional for the test scenario; SSH/22 is constrained to operator-provided CIDRs only.
- The `rust_poa_zkp_voting` project does **not** implement a real zero-knowledge proof. The README labels the eligibility commitment as a placeholder pattern, not a ZKP. This is documented, not a bug.
- The LLM-based projects (`rag_assistant`, `agent_toolkit`, `llm_eval_harness`, `nlp_text_summarization_api`) send user prompts to OpenAI when configured with an API key. If you supply your own key, your usage is governed by OpenAI's terms; the projects do nothing to obfuscate or redact prompts before sending them.

## Patterns I take seriously

- **Anything that lets a clone of the repository access a real account.** Committed SSH keys, AWS credentials, OpenAI keys, Terraform state with embedded secrets, `.env` files with real values. See the next section.
- **Anything that lets a user of the public Flask APIs (`rag_assistant`, `predictive_maintenance`, `nlp_text_summarization_api`) escalate beyond what's documented.** Path traversal, unbounded resource consumption, dependency-driven RCE.
- **Cryptographic primitive misuse** in the blockchain projects. The Rust crates explicitly claim to use SHA-256 / Ed25519 / constant-time comparison; if any of those is implemented incorrectly, that's a real bug even in a simulation.
- **`tool` decorator in `agent_toolkit`** lets the LLM call Python functions you've registered. If the built-in tools (`calculator`, `read_file`, `list_directory`) can be coerced into executing arbitrary code or reading unintended files, that's in scope.

## What I won't do

- Track or fingerprint users. The Flask projects expose `/health` and a single endpoint each; none log IPs or per-request metadata beyond what's needed to serve the response.
- Send analytics or telemetry to any third party from any project in this repo.

## Secrets, keys, and credentials

This repository must never contain:

- `.pem`, `.key`, `.pfx`, `.p12` files (SSH keys, TLS keys, PKCS12 bundles)
- `.tfstate` / `.tfstate.backup` (Terraform state — often contains secrets)
- `.env` files with real values (only `.env.example` templates are committed)
- API keys, OAuth client secrets, JWT signing keys
- Database connection strings with embedded passwords

The `.gitignore` is configured to exclude all of the above by default. If you find one of these in the repo, that's a security report.

## Coordinated disclosure

I prefer coordinated disclosure: report privately first, agree on a timeline, then make the report public after a fix is in place. If you've followed the reporting steps above and want public credit, I'll list you in the relevant project's commit message and changelog.

## Contact

[lmdixon23@gmail.com](mailto:lmdixon23@gmail.com)
