"""set_targets tool Lambda. Layer 5: re-validates with limits.py even if the hook was bypassed."""
import os
from datetime import UTC, datetime
from decimal import Decimal

from ppa import limits
from ppa.identity import get_user_id

_ddb = None


def _table():
    global _ddb
    if _ddb is None:
        import boto3
        _ddb = boto3.resource("dynamodb")
    return _ddb.Table(os.environ["TARGETS_TABLE"])


def handler(event, context=None):
    try:
        user_id = get_user_id(context)
        kcal, protein, budget = limits.validate_targets(
            event.get("calories_kcal"), event.get("protein_g"), event.get("weekly_budget_php"))
    except limits.RuleViolation as v:
        return {"status": "denied", "rule": v.rule_id, "message": v.message}

    _table().put_item(Item={
        "user_id": user_id,  # always from identity, never from event
        "calories_kcal": Decimal(str(kcal)),
        "protein_g": Decimal(str(protein)),
        "weekly_budget_php": Decimal(str(budget)),
        "updated_at": datetime.now(UTC).isoformat(),
    })
    return {"status": "ok", "calories_kcal": kcal, "protein_g": protein, "weekly_budget_php": budget}