import math

import pytest

from ppa import limits as L


@pytest.mark.parametrize("kcal,rule", [(800, "R2-CALORIE-FLOOR"), (1399, "R2-CALORIE-FLOOR"), (6000, "R2-CALORIE-CEILING")])
def test_calorie_bounds(kcal, rule):
    with pytest.raises(L.RuleViolation) as e:
        L.validate_targets(kcal, 100, 1500)
    assert e.value.rule_id == rule

def test_valid_targets():
    assert L.validate_targets(2000, 100, 1500) == (2000.0, 100.0, 1500.0)

@pytest.mark.parametrize("bad", [True, "2000", None, math.nan, math.inf])
def test_rejects_non_numbers(bad):
    with pytest.raises(L.RuleViolation):
        L.validate_targets(bad, 100, 1500)

def test_protein_and_budget_ranges():
    with pytest.raises(L.RuleViolation): L.validate_targets(2000, 400, 1500)
    with pytest.raises(L.RuleViolation): L.validate_targets(2000, 100, 50)

def test_price_band():
    assert L.check_price_update(100, 120) == "ok"
    assert L.check_price_update(100, 300) == "needs_confirmation"
    assert L.check_price_update(100, 10) == "needs_confirmation"
    assert L.check_price_update(None, 100) == "ok"
    with pytest.raises(L.RuleViolation): L.check_price_update(100, -5)
    
def test_price_band_ignores_nonpositive_old_price():
    assert L.check_price_update(0, 100) == "ok"