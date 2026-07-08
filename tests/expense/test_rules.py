from lib.expense.rules import (
    CATEGORIES, Rule, default_rules, load_rules, dump_rules, validate_category,
    classify, classify_rows,
)
from lib.expense.models import Row

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

def _h(shop):
    return Row(date="d", shop=shop, usd=1, idr=0, krw=1, user="", source="haewoe", card_no="1")

def _g(industry):
    return Row(date="d", shop="X", usd=0, idr=0, krw=1, user="", source="gukne", card_no="1", industry=industry)

def test_classify_haewoe_keyword():
    rules = default_rules()
    assert classify(_h("MCDONALD'S F39732"), rules) == "식비"
    assert classify(_h("WAWA 6309"), rules) == "여비교통비"     # 순서: 마트 뒤 주유 먼저
    assert classify(_h("FASTENAL COMPANY"), rules) == "소모품비"

def test_classify_mart_blank():
    assert classify(_h("FOOD LION #2811"), default_rules()) == ""

def test_classify_code_regex_blank():
    assert classify(_h("EOC03171"), default_rules()) == ""

def test_classify_gukne_uses_industry():
    assert classify(_g("편의점"), default_rules()) == "식비"

def test_classify_rows_sets_category():
    rows = [_h("MCDONALD'S"), _h("FOOD LION")]
    out = classify_rows(rows, default_rules())
    assert out[0].category == "식비"
    assert out[1].category == ""
