from datetime import date

from app import shelf_life


def test_known_category():
    assert shelf_life.days("carne", "chiuso") == 3
    assert shelf_life.estimate("carne", "chiuso", date(2026, 10, 1)) == date(2026, 10, 4)


def test_unknown_category_falls_back_to_default():
    assert shelf_life.days("alieni", "aperto") == 3
