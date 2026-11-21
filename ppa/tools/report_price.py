"""report_price tool Lambda. Layers 5 and 7: outliers are not applied, they need confirmation (E2)."""
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
    return _ddb.Table(os.environ["PRICES_TABLE"])


def handler(event, context=None):
    try:
        user_id = get_user_id(context)
        item_id = event.get("item_id")
        if not isinstance(item_id, str) or not 0 < len(item_id) <= 64:
            raise limits.RuleViolation("E2-ITEM-INVALID", "item_id must be a short string.")
        store = str(event.get("store", ""))[:80]  # E8: free text is data only, stored, never executed
        table = _table()
        existing = table.get_item(Key={"item_id": item_id}).get("Item")
        old = float(existing["price_php"]) if existing else None
        new = float(limits._num(event.get("new_price"), "new_price"))
        verdict = limits.check_price_update(old, new)
    except limits.RuleViolation as v:
        return {"status": "denied", "rule": v.rule_id, "message": v.message}

    if verdict == "needs_confirmation":
        return {"status": "needs_confirmation", "item_id": item_id, "old_price": old, "new_price": new}

    table.put_item(Item={
        "item_id": item_id, "price_php": Decimal(str(new)), "store": store,
        "reported_by": user_id, "updated_at": datetime.now(UTC).isoformat(),
    })
    return {"status": "ok", "item_id": item_id, "price_php": new}