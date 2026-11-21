# Contributing and CI/CD flow

- `main` is protected: changes arrive by pull request, CI must pass.
- Branch names: `feat/...`, `fix/...`, `docs/...`. Commits follow Conventional Commits (`fix: ...`).
- Any change to a rule must update **three places in the same PR**: `RULES.md`, `ppa/limits.py` (or the hook), and a test.
- CI (`.github/workflows/ci.yml`): lint, unit tests, adversarial replay (fails if any case changes outcome), hooks.json validation, and a check that `docs/STRESS_RESULTS.md` is up to date.
- CD: pushes to `main` package the hook Lambda and, if the `AWS_DEPLOY_ROLE_ARN` repository variable is set, deploy it via GitHub OIDC (no long-lived keys). Without it the job only builds the artifact.
