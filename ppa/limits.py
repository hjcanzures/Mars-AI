"""Hard limits for Mars (single source of truth).

These numbers live in code, not in the prompt. Both the lifecycle hook and the
tool Lambdas import this module, so a rule can't be argued away by the model.
Each violation carries the rule ID used in RULES.md and the stress-test log.
"""
import math

CALORIE_MIN_KCAL = 1400
CALORIE_MAX_KCAL = 4000
PROTEIN_MIN_G = 30
PROTEIN_MAX_G = 220
WEEKLY_BUDGET_MIN_PHP = 200
WEEKLY_BUDGET_MAX_PHP = 20000
PRICE_CONFIRM_BAND = (0.5, 2.0)   # new/old outside this -> needs human confirmation
MAX_SERVINGS_PER_LOG = 10


class RuleViolation(Exception):
    def __init__(self, rule_id: str, message: str):
        super().__init__(message)
        self.rule_id = rule_id
        self.message = message


def _num(value, field):
    # bool is an int subclass in Python; reject it explicitly.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuleViolation("R2-INPUT", f"{field} must be a number")
    if math.isnan(value) or math.isinf(value):
        raise RuleViolation("R2-INPUT", f"{field} must be finite")
    return float(value)


def validate_targets(calories_kcal, protein_g, weekly_budget_php):
    kcal = _num(calories_kcal, "calories_kcal")
    if kcal < CALORIE_MIN_KCAL:
        raise RuleViolation("R2-CALORIE-FLOOR", f"Daily calories below {CALORIE_MIN_KCAL} kcal are not supported.")
    if kcal > CALORIE_MAX_KCAL:
        raise RuleViolation("R2-CALORIE-CEILING", f"Daily calories above {CALORIE_MAX_KCAL} kcal are not supported.")
    prot = _num(protein_g, "protein_g")
    if not PROTEIN_MIN_G <= prot <= PROTEIN_MAX_G:
        raise RuleViolation("R2-PROTEIN-RANGE", f"Protein target must be {PROTEIN_MIN_G}-{PROTEIN_MAX_G} g/day.")
    budget = _num(weekly_budget_php, "weekly_budget_php")
    if not WEEKLY_BUDGET_MIN_PHP <= budget <= WEEKLY_BUDGET_MAX_PHP:
        raise RuleViolation("R2-BUDGET-RANGE", f"Weekly budget must be PHP {WEEKLY_BUDGET_MIN_PHP}-{WEEKLY_BUDGET_MAX_PHP}.")
    return kcal, prot, budget


def check_price_update(old_price, new_price):
    """Return 'ok' or 'needs_confirmation'. Non-positive prices are rejected."""
    new = _num(new_price, "new_price")
    if new <= 0:
        raise RuleViolation("E2-PRICE-INVALID", "Price must be positive.")
    if old_price is None:
        return "ok"
    old = _num(old_price, "old_price")
    ratio = new / old
    lo, hi = PRICE_CONFIRM_BAND
    return "ok" if lo <= ratio <= hi else "needs_confirmation"


def validate_servings(servings):
    s = _num(servings, "servings")
    if not 0 < s <= MAX_SERVINGS_PER_LOG:
        raise RuleViolation("A2-SERVINGS", f"Servings must be above 0 and at most {MAX_SERVINGS_PER_LOG}.")
    return s
