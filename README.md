# Mars

An AI agent for budget-aware meal planning, protein optimization, food expense tracking, and adaptive grocery recommendations.

Built on the Amazon Bedrock AgentCore managed harness. The problem: students need to stretch a small budget for meals that keep them full. Getting this wrong matters (crash diets, bad medical or supplement advice, unwanted purchases), so Mars has hard limits that are enforced in code, not just in the prompt.

- **Repo:** <add GitHub link>
- **Demo / screenshots:** <add link>, plus `docs/screenshots/`

**Start here**
- Rules and how each is enforced: [RULES.md](RULES.md)
- System flow diagrams: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Stress test (automated results + live runs): [docs/STRESS_TEST.md](docs/STRESS_TEST.md), [docs/STRESS_RESULTS.md](docs/STRESS_RESULTS.md)
- What broke and how it was fixed: [docs/BUILD_LOG.md](docs/BUILD_LOG.md)
- Contributing / branch and CI flow: [CONTRIBUTING.md](CONTRIBUTING.md)

## How it stays inside its limits
Eight layers, from deterministic to prompt-level: input hook with Unicode normalization and injection screen, Bedrock Guardrail, tool-call hook allowlist, no purchase/shell/browser tool attached, tool-side re-validation, table-scoped IAM, human confirmation for outlier prices, and the system prompt. The prompt is the last line of defence, never the only one. See [RULES.md](RULES.md).

## Run locally
```bash
pip install -r requirements-dev.txt
python -m pytest              # boundary tests for limits, hook and tools
python scripts/run_stress.py  # replays adversarial cases, regenerates docs/STRESS_RESULTS.md
```

## Layout
```
ppa/limits.py           hard limits, single source of truth
ppa/boundary_hook.py    lifecycle-hook Lambda (input gate + tool gate)
ppa/identity.py         caller identity (never from tool arguments)
ppa/tools/              tool Lambdas (set_targets, report_price)
infra/template.yaml     DynamoDB tables, tool Lambdas
infra/hooks.json        hook wiring, failureMode=deny
tests/                  unit tests for limits, hook and tools
scripts/run_stress.py   adversarial replay used by CI
.github/workflows/      CI/CD
docs/                   architecture, stress tests, build log
```

`ppa` is the original working name of the package (ProteinPeso).