# Mars: a budget protein planner agent that can't be talked out of its rules

![CI](https://github.com/OWNER/proteinpeso/actions/workflows/ci.yml/badge.svg)

Amazon Bedrock AgentCore managed harness. Student cost-of-living problem: hit your protein target for the least pesos.

**Start here**
- Rules and how each is enforced: [RULES.md](RULES.md)
- System flow diagrams: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Stress test (automated results + live runs): [docs/STRESS_TEST.md](docs/STRESS_TEST.md), [docs/STRESS_RESULTS.md](docs/STRESS_RESULTS.md)
- What broke and how it was fixed: [docs/BUILD_LOG.md](docs/BUILD_LOG.md)
- Contributing / branch and CI flow: [CONTRIBUTING.md](CONTRIBUTING.md)

## Run locally
```bash
pip install -r requirements-dev.txt
python -m pytest            # 26 boundary tests
python scripts/run_stress.py  # replays adversarial cases, regenerates docs/STRESS_RESULTS.md
```

## Layout
```
ppa/limits.py          hard limits, single source of truth
ppa/boundary_hook.py   lifecycle-hook Lambda (input gate + tool gate)
infra/hooks.json       hook wiring, failureMode=deny
tests/                 unit tests for limits and hook
scripts/run_stress.py  adversarial replay used by CI
.github/workflows/     CI/CD
```
