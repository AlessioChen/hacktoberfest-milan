from datetime import date

import pytest

from app import dates


@pytest.mark.parametrize("text,expected", [
    ("EXP 12/10/26", date(2026, 10, 12)),
    ("12.10.2026", date(2026, 10, 12)),
    ("da consumarsi entro 05-11-2026", date(2026, 11, 5)),
    ("TMC 03/2027", date(2027, 3, 31)),
    ("niente", None),
    ("32/13/2026", None),
])
def test_parse(text, expected):
    assert dates.parse(text) == expected


def test_kind():
    assert dates.kind("da consumarsi preferibilmente entro") == "soft"
    assert dates.kind("da consumare entro") == "hard"
    assert dates.kind("12/10") == "unknown"


@pytest.mark.parametrize("text,expected", [
    ("2026-10-12", date(2026, 10, 12)),
    ("12 10 2026", date(2026, 10, 12)),
    ("12/OCT/26", date(2026, 10, 12)),
    ("12 OTT 2026", date(2026, 10, 12)),
    ("OTT 2026", date(2026, 10, 31)),
    ("12102026", date(2026, 10, 12)),
    ("12/10", None),
    ("L:2610A 12/10", None),
    ("L 261026 EXP 12/10/26", date(2026, 10, 12)),
    ("Conf. 01/10/26 Scad. 12/10/26", date(2026, 10, 12)),
    ("BB 05.28", date(2028, 5, 31)),
])
def test_parse_variants(text, expected):
    assert dates.parse(text) == expected


def test_old_full_dates_still_parse():
    assert dates.parse("15 04 11") == date(2011, 4, 15)
    assert dates.parse("20/01/23 H 11:00:49 L.885220") == date(2023, 1, 20)
