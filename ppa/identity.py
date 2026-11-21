"""Resolve the caller's user ID. Never read it from tool arguments (rule A1)."""
from ppa.limits import RuleViolation


def get_user_id(context) -> str:
    custom = getattr(getattr(context, "client_context", None), "custom", None) or {}
    user_id = custom.get("user_id")
    if not isinstance(user_id, str) or not user_id.strip():
        raise RuleViolation("A1-NO-IDENTITY", "No authenticated user on this request.")
    return user_id