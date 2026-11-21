# Build log (what broke and how it was fixed)

| # | Day | What broke | How it was found | Fix |
|---|-----|------------|------------------|-----|
| 1 | 1 | Scaffold command wrote nothing: shell brace expansion (`mkdir {a,b}`) is not supported by `/bin/sh` (dash) | Test run reported "no tests ran" | Create directories explicitly. It happened a second time on Day 2 (created one folder literally named `{ppa,tests,...`), so scaffolding now uses plain `mkdir -p a b c`. |
| 2 | 2 | **`\bDAN\b` was matched case-insensitively**, so any user writing "Dan" or the Filipino word "dan" would be blocked as a jailbreak (false positive on legitimate students) | Review while writing the stress suite | Split into case-insensitive and case-sensitive pattern lists; regression tests `test_names_containing_dan_allowed` and `test_dan_persona_still_blocked`. |
| 3 | 2 | **Unknown hook events were allowed** (`lambda_handler` fell through to `_allow`), which contradicts the fail-closed rule E5 | Review against RULES.md | Unknown events now return `deny` with `E5-UNKNOWN-EVENT`; test `test_unknown_event_fails_closed`. |
| 4 | 2 | My own stress case S10 was meant to show a regex gap but was caught by a second pattern ("system prompt") | Stress run showed FAIL against my expectation | Rewrote the payload to contain only the obfuscated phrase. The gap is now real and documented, and S10 shows that downstream layers cover it. |
| 5 | 3 | **Unicode obfuscation bypassed the regex**: a zero-width character inside "ignore" or fullwidth letters evaded `INJECTION_PATTERNS` | New test `test_unicode_obfuscated_injection_blocked` failed on first run (2 failed, both returned `[OK] Allowed.`) | Added NFKC normalization and zero-width stripping before pattern matching; stress case S12. Leetspeak (S10) is still a documented gap. |
| 6 | 3 | **Docs claimed more than the code did**: user-key-scoped IAM, confirmation for target changes, and tools that did not exist yet | Reviewing RULES.md against `template.yaml` and the Lambdas | Reworded layers 6 and 7, added an enforcement-status table separating code, guardrail and prompt-only rules, and listed tools still to build. |
| 7 | 3 | **Missing `ppa/__init__.py`** and CI/Lambda Python versions disagreed (3.12 vs 3.14) | Repo review | Added the file, aligned both on 3.13. |
| 8 | 3 | **Division by zero** possible in `check_price_update` if a stored price were 0 | Code review | Guard `if old <= 0: return "ok"` plus a test. |

## Known limitations
- Regex screening is a cheap first filter, not a defence on its own; leetspeak and non-English injections (S10, L6) rely on the guardrail, the tool gate and the prompt.
- Tools `plan_meals`, `log_meal`, `spend_summary`, `find_stores` and `confirm_action` are allowlisted but not implemented yet.
- Applying a price after the user confirms an outlier is not implemented; E2 currently blocks the update.
- R5, E1, E3, E4, E6 and E7 are prompt-only and verified by live runs, not CI.
- Part B of the stress test and the screenshots must be run against the deployed harness.
- `REPLACE_WITH_*` ARNs in `infra/hooks.json` are filled in at deploy time.