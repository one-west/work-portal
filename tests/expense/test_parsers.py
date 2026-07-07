from lib.expense.parsers import to_number

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
