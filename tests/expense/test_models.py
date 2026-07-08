from lib.expense.models import Row, Meta, CardInfo

def test_row_defaults():
    r = Row(date="2026.06.02", shop="ENMARKET", usd=41.65, idr=0,
            krw=64936, user="공용", source="haewoe", card_no="4074672197393852")
    assert r.category == ""
    assert r.detail == ""
    assert r.industry == ""

def test_meta_defaults():
    m = Meta(traveler="김동현")
    assert m.usd_rate == 0.0
    assert m.region == ""

def test_cardinfo():
    c = CardInfo(card_no="4074672197393852", traveler="김동현", region="미국 조지아", label="해외출장4")
    assert c.traveler == "김동현"
