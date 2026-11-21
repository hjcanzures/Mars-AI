"""AgentCore harness lifecycle-hook Lambda: the deterministic boundary gate.

Handles two events (failureMode=deny in infra/hooks.json, so errors fail closed):
  before_invocation  - shape check, injection pre-screen, Bedrock Guardrail (ApplyGuardrail)
  before_tool_call   - tool allowlist, tool-type allowlist, argument validation

Returns {"decision": "allow"|"deny", "reason": "..."} as the harness expects.
Every decision is logged as one JSON line (rule ID + layer) for the stress-test evidence.
"""
import json
import logging
import os
import re

from ppa import limits

log = logging.getLogger()
log.setLevel(logging.INFO)

GUARDRAIL_ID = os.environ.get("GUARDRAIL_ID", "")
GUARDRAIL_VERSION = os.environ.get("GUARDRAIL_VERSION", "DRAFT")
MAX_PROMPT_CHARS = 2000

# No purchase tool exists at all. Anything not listed here is denied.
ALLOWED_TOOLS = frozenset({
    "set_targets", "plan_meals", "log_meal", "spend_summary",
    "report_price", "find_stores", "confirm_action",
})
# No builtin (shell/files), no remote_mcp, no browser, no code interpreter.
ALLOWED_TOOL_TYPES = frozenset({"agentcore_gateway", "inline_function"})

# Case-insensitive patterns.
INJECTION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in (
    r"ignore (all |any |the )?(previous|prior|above|earlier) (instructions|rules|prompts?)",
    r"disregard (your|the|all) (rules|instructions|guidelines|limits)",
    r"(reveal|print|show|repeat) (me )?(your|the) (system|hidden|initial) (prompt|instructions)",
    r"\bdeveloper mode\b|\bjailbreak\b",
    r"you are no longer|new instructions:|override (the )?(safety|rules|limits)",
)]
# Case-SENSITIVE: "DAN" the jailbreak persona. Matching it case-insensitively
# blocked ordinary users named Dan (see docs/BUILD_LOG.md, bug #2).
INJECTION_PATTERNS_CASE_SENSITIVE = [re.compile(r"\bDAN\b")]

_client = None


def _bedrock():
    global _client
    if _client is None:
        import boto3  # lazy: keeps unit tests dependency-free
        _client = boto3.client("bedrock-runtime")
    return _client


def _decide(decision, rule, layer, reason, event):
    log.info(json.dumps({
        "decision": decision, "rule": rule, "layer": layer,
        "event": event.get("event"), "session": event.get("sessionId"),
        "tool": (event.get("context") or {}).get("toolName"),
    }))
    return {"decision": decision, "reason": f"[{rule}] {reason}"[:1024]}


def _allow(event):
    return _decide("allow", "OK", "hook", "Allowed.", event)


def before_invocation(event):
    ctx = event["context"]
    if ctx.get("truncated"):
        return _decide("deny", "R4-TRUNCATED", "hook", "Request too large to evaluate.", event)

    messages = ctx.get("messages") or []
    # Only one fresh user turn per call. History comes from session state, so a client
    # that sends assistant turns or toolUse/toolResult blocks is forging context.
    if len(messages) != 1 or messages[0].get("role") != "user":
        return _decide("deny", "R4-FORGED-HISTORY", "hook", "Send exactly one user message.", event)

    texts = []
    for block in messages[0].get("content", []):
        if set(block.keys()) != {"text"}:
            return _decide("deny", "R4-NONTEXT-BLOCK", "hook", "Only plain text is accepted.", event)
        texts.append(block["text"])
    prompt = "\n".join(texts)

    if len(prompt) > MAX_PROMPT_CHARS:
        return _decide("deny", "R4-TOO-LONG", "hook", "Message too long.", event)

    for pat in INJECTION_PATTERNS + INJECTION_PATTERNS_CASE_SENSITIVE:
        if pat.search(prompt):
            return _decide("deny", "R4-INJECTION", "hook-regex", "Instruction-override attempt blocked.", event)

    if GUARDRAIL_ID:
        try:
            resp = _bedrock().apply_guardrail(
                guardrailIdentifier=GUARDRAIL_ID, guardrailVersion=GUARDRAIL_VERSION,
                source="INPUT", content=[{"text": {"text": prompt}}],
            )
        except Exception as exc:  # noqa: BLE001  intentional: any failure must fail closed
            return _decide("deny", "R4-GUARDRAIL-ERROR", "guardrail", f"Safety check unavailable ({type(exc).__name__}).", event)
        if resp.get("action") == "GUARDRAIL_INTERVENED":
            return _decide("deny", "R3-GUARDRAIL", "guardrail", "Blocked by safety policy (medical/supplement/attack).", event)

    return _allow(event)


def before_tool_call(event):
    ctx = event["context"]
    name = str(ctx.get("toolName", "")).split("___")[-1]  # gateway prefixes target name
    if ctx.get("toolType") not in ALLOWED_TOOL_TYPES:
        return _decide("deny", "A4-TOOL-TYPE", "hook", "Tool type not permitted.", event)
    if name not in ALLOWED_TOOLS:
        return _decide("deny", "R1-TOOL-NOT-ALLOWED", "hook", "No such capability.", event)

    args = ctx.get("toolInput")
    if not isinstance(args, dict) or args.get("truncated") is True:
        return _decide("deny", "R4-BAD-TOOL-INPUT", "hook", "Tool input unreadable.", event)

    try:
        if name == "set_targets":
            limits.validate_targets(args["calories_kcal"], args["protein_g"], args["weekly_budget_php"])
        elif name == "log_meal":
            limits.validate_servings(args["servings"])
        elif name == "report_price":
            limits.check_price_update(None, args["new_price"])
    except limits.RuleViolation as v:
        return _decide("deny", v.rule_id, "hook", v.message, event)
    except (KeyError, TypeError):
        return _decide("deny", "R4-BAD-TOOL-INPUT", "hook", "Missing or malformed tool arguments.", event)

    return _allow(event)


def lambda_handler(event, _context=None):
    kind = event.get("event")
    if kind == "before_invocation":
        return before_invocation(event)
    if kind == "before_tool_call":
        return before_tool_call(event)
    # Unknown event types fail closed (E5), not open.
    return _decide("deny", "E5-UNKNOWN-EVENT", "hook", "Unrecognised hook event.", event)
