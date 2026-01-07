from utils import dates_match

def test_dates_match_true():
    assert dates_match("202510", "10/1/2025") is True

def test_dates_match_false_month():
    assert dates_match("202510", "09/30/2025") is False

def test_dates_match_false_year():
    assert dates_match("202510", "10/1/2024") is False

def test_dates_match_invalid_format():
    assert dates_match("202510", "10-1-2025") is False
