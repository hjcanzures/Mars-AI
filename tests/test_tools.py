from types import SimpleNamespace

import pytest

from ppa.tools import report_price, set_targets


class FakeTable:
    def __init__(self, key):
        self.key, self.items = key, {}

    def get_item(self, Key):
        item = self.items.get(Key[self.key])
        return {"Item": item} if item else {}

    def put_item(self, Item):
        self.items[Item[self.key]] = Item


Ctx = SimpleNamespace(client_context=SimpleNamespace(custom={"user_id": "u1"}))
NoUser = SimpleNamespace(client_context=None)


@pytest.fixture
def targets(monkeypatch):
    t = FakeTable("user_id")
    monkeypatch.setattr(set_targets, "_table", lambda: t)
    return t


@pytest.fixture
def prices(monkeypatch):
    t = FakeTable("item_id")
    monkeypatch.setattr(report_price, "_table", lambda: t)
    return t


GOOD = {"calories_kcal": 2000, "protein_g": 100, "weekly_budget_php": 1500}


def test_set_targets_ok(targets):
    assert set_targets.handler(GOOD, Ctx)["status"] == "ok"
    assert "u1" in targets.items


def test_set_targets_rejects_crash_diet_without_hook(targets):
    r = set_targets.handler({**GOOD, "calories_kcal": 700}, Ctx)
    assert r["status"] == "denied" and r["rule"] == "R2-CALORIE-FLOOR"
    assert targets.items == {}


def test_set_targets_ignores_user_id_in_args(targets):
    set_targets.handler({**GOOD, "user_id": "victim"}, Ctx)
    assert list(targets.items) == ["u1"]


def test_set_targets_requires_identity(targets):
    assert set_targets.handler(GOOD, NoUser)["rule"] == "A1-NO-IDENTITY"


def test_report_price_negative_denied(prices):
    r = report_price.handler({"item_id": "egg", "new_price": -5}, Ctx)
    assert r["rule"] == "E2-PRICE-INVALID" and prices.items == {}


def test_report_price_outlier_not_applied(prices):
    report_price.handler({"item_id": "egg", "new_price": 100}, Ctx)
    r = report_price.handler({"item_id": "egg", "new_price": 300}, Ctx)
    assert r["status"] == "needs_confirmation"
    assert float(prices.items["egg"]["price_php"]) == 100.0


def test_report_price_normal_update(prices):
    report_price.handler({"item_id": "egg", "new_price": 100}, Ctx)
    assert report_price.handler({"item_id": "egg", "new_price": 120}, Ctx)["status"] == "ok"