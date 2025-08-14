import pytest
from unittest.mock import patch, Mock

import parser as p


def test_normalize_fio():
    assert p.normalize_fio("иван  иВаноВ") == "Иван Иванов"


def test_validate_birthdate_ok():
    dt = p.validate_birthdate("01-12-2000")
    assert dt.year == 2000 and dt.day == 1 and dt.month == 12


def test_validate_birthdate_bad():
    with pytest.raises(ValueError):
        p.validate_birthdate("2000-12-01")


@patch("parser.requests.get")
@patch("parser.requests.head")
def test_find_olymps_parses_entries(head_mock: Mock, get_mock: Mock):
    head_mock.return_value = Mock(status_code=200)
    get_mock.return_value = Mock(
        status_code=200,
        text=(
            "diplomaCodes = [\n"
            "{oa: '№1. \'Олимпиада\' (\'Профиль\'), 1 уровень. Диплом 1 степени.', name: 'X', form: 11, hashed: 'h'},\n"
            "];\n"
        ),
    )

    results = p.find_olymps("Иванов Иван", "01-12-2000", years_back=1)
    assert len(results) >= 1
    r = results[0]
    print("DEBUG_ENTRY:", r)
    assert r["olymp_name"] == "Олимпиада"
    assert r["profile"] == "Профиль"
    assert r["level"] == 1
    assert r["result"] in (0, 1)