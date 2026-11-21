# Build log (what broke and how it was fixed)

| # | Day | What broke | How it was found | Fix |
|---|-----|------------|------------------|-----|
| 1 | 1 | Scaffold command wrote nothing: shell brace expansion (`mkdir {a,b}`) is not supported by `/bin/sh` (dash) | Test run reported "no tests ran" | Create directories explicitly. It happened a second time on Day 2 (created one folder literally named `{ppa,tests,...`), so scaffolding now uses plain `mkdir -p a b c`. |
| 2 | 2 | **`\bDAN\b` was matched case-insensitively**, so any user writing "Dan" or the Filipino word "dan" would be blocked as a jailbreak (false positive on legitimate students) | Review while writing the stress suite | Split into case-insensitive and case-sensitive pattern lists; regression tests `test_names_containing_dan_allowed` and `test_dan_persona_still_blocked`. |
| 3 | 2 | **Unknown hook events were allowed** (`lambda_handler` fell through to `_allow`), which contradicts the fail-closed rule E5 | Review against RULES.md | Unknown events now return `deny` with `E5-UNKNOWN-EVENT`; test `test_unknown_event_fails_closed`. |
| 4 | 2 | My own stress case S10 was meant to show a regex gap but was caught by a second pattern ("system prompt") | Stress run showed FAIL against my expectation | Rewrote the payload to contain only the obfuscated phrase. The gap is now real and documented, and S10 shows that downstream layers cover it. |

## Known limitations
- Regex screening is a cheap first filter, not a defence on its own; obfuscated injections (S10) are handled by the guardrail, the tool gate and the prompt.
- Part B of the stress test (live agent) and the screenshots still need to be run against the deployed harness.
- `REPLACE_WITH_*` ARNs in `infra/hooks.json` are filled in at deploy time.
