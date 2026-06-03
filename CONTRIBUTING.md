# Contributing

This is a portfolio repository. Most projects are scoped somewhere between "working experiment" and "production system" — contributions that move them in either direction are welcome, but please open an issue first so we can align before you invest time.

## Ground rules

- **Open an issue first.** Non-trivial PRs (new features, dependency upgrades, architectural changes) should start with an issue describing what you want to change and why. One-line fixes (typo, broken link, obvious bug) can go straight to a PR.
- **One project per PR.** Each project (`ai_engineering/rag_assistant/`, `blockchain_protocols/rust_decentralized_voting/`, etc.) has its own dependency surface and CI matrix entry. Mixing changes across projects makes review hard.
- **Match the existing style of the project you're touching.** Python projects use `argparse`, `dataclasses`, and `httpx`. Rust projects use `thiserror`, `lib + bin` layout, and `tests/` for integration tests. Don't add a new framework without discussion.
- **Tests are not optional.** If you change behavior, add or update a test. The CI workflow in `.github/workflows/ci.yml` will run them; a green CI is the bar for merge.
- **Match the README structure.** Per-project READMEs follow a consistent section order. If you add a project, follow that same order — any existing README shows the pattern.

## Local setup

Each project has its own `requirements.txt` (Python), `Cargo.toml` (Rust), or per-tool prerequisites. The standard pattern is:

```bash
cd <project>
pip install -r requirements.txt        # Python
# or
cargo build                            # Rust
```

For Python projects, please use a fresh virtualenv (`python -m venv venv`). The repo's `.gitignore` covers `venv/`, `.venv/`, and `env/`, so your environment won't accidentally land in a commit.

## Tests

```bash
# Python
python -m pytest tests/                # or `python -m unittest discover tests`

# Rust
cargo test
```

Each project's README includes its specific test invocation under **Getting Started -> Testing**.

## Pull request checklist

Before opening a PR:

1. [ ] The CI for your project is green locally.
2. [ ] New or changed behavior is covered by a test.
3. [ ] The project's README is updated if you changed its public interface or its claims.
4. [ ] No secrets, `.pem` files, `.tfstate`, `.env`, or `venv/` directories are in your diff. See `SECURITY.md`.
5. [ ] Commit messages are descriptive (`fix:`, `feat:`, `chore:` prefixes preferred but not required).

## What "honest scoping" means in this repo

Every project README has a **Scope** section. This is deliberate — the repo's stance is that an honest "this is a simulation, not a production system" caveat is more credible than fake claims of completeness. If your contribution changes what a project does, please update that section to match.

## License

By contributing you agree that your contribution will be licensed under the same MIT License that covers the rest of the repository (see [LICENSE](./LICENSE)).

## Questions

Open an issue, or email lmdixon23@gmail.com.
