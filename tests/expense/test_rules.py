from lib.expense.rules import (
    CATEGORIES, Rule, default_rules, load_rules, dump_rules, validate_category,
)

def test_categories_has_expected():
    for c in ["식비", "여비교통비", "소모품비", "접대비", "항공료"]:
        assert c in CATEGORIES

def test_default_rules_nonempty_and_ordered():
    rules = default_rules()
    assert len(rules) > 0
    orders = [r.order for r in rules]
    assert orders == sorted(orders)

def test_json_roundtrip():
    rules = default_rules()
    obj = dump_rules(rules)
    back = load_rules(obj)
    assert [r.keyword for r in back] == [r.keyword for r in rules]
    assert [r.category for r in back] == [r.category for r in rules]

def test_validate_category():
    assert validate_category("식비") is True
    assert validate_category("") is True          # 공란 허용
    assert validate_category("없는항목") is False
