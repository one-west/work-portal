from lib.expense.parsers import to_number, normalize_card_no, extract_cards, normalize_haewoe, normalize_gukne
from lib.expense.models import Row
import pandas as pd

def test_plain_number():
    assert to_number("64,936") == 64936.0

def test_decimal():
    assert to_number("41.65") == 41.65

def test_triangle_negative():
    assert to_number("△1,200") == -1200.0
    assert to_number("▲500") == -500.0

def test_paren_negative():
    assert to_number("(1,000)") == -1000.0

def test_unicode_space():
    assert to_number(" 1,234　") == 1234.0

def test_blank_and_dash():
    assert to_number("") is None
    assert to_number("-") is None
    assert to_number(None) is None

def test_normalize_card_no():
    assert normalize_card_no("4074-6721-9739-3852") == "4074672197393852"
    assert normalize_card_no("4074 6721 9739 3852") == "4074672197393852"

def _row(card):
    return Row(date="2026.06.02", shop="X", usd=1, idr=0, krw=1,
               user="공용", source="haewoe", card_no=card)

def test_extract_cards_unique_ordered():
    rows = [_row("111"), _row("222"), _row("111")]
    assert extract_cards(rows) == ["111", "222"]

def test_normalize_haewoe():
    df = pd.DataFrame([
        {"승인일": "2026.06.27", "가맹점명": "ENMARKET 1330", "카드번호": "4074-6721-9739-3852",
         "이용자명": "공용", "현지이용금액": "41.65", "결제원금": "64,936"},
    ])
    rows = normalize_haewoe(df)
    assert len(rows) == 1
    r = rows[0]
    assert r.source == "haewoe"
    assert r.card_no == "4074672197393852"
    assert r.usd == 41.65
    assert r.idr == 0
    assert r.krw == 64936.0
    assert r.shop == "ENMARKET 1330"
    assert r.user == "공용"

def test_normalize_gukne_maps_and_filters_cancel():
    df = pd.DataFrame([
        {"승인일": "2026.06.01", "가맹점명": "GS25", "업종명": "편의점", "카드번호": "111",
         "이용자명": "공용", "승인금액": "10,000", "상태": "정상"},
        {"승인일": "2026.06.02", "가맹점명": "취소건", "업종명": "편의점", "카드번호": "111",
         "이용자명": "공용", "승인금액": "5,000", "상태": "취소"},
    ])
    rows = normalize_gukne(df)
    assert len(rows) == 1          # 취소건 제외
    r = rows[0]
    assert r.source == "gukne"
    assert r.industry == "편의점"
    assert r.krw == 10000.0
    assert r.usd == 0 and r.idr == 0
