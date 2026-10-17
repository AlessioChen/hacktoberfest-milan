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
