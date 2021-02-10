
import pytest
from django.test import TestCase


from flat_crawler.utils.text_utils import deduce_size_from_text, parse_timedelta_str_to_seconds
from flat_crawler.constants import MINUTE, HOUR, DAY


BASE_PRICE = 300000

@pytest.mark.parametrize(
    "text, price, result", [
        ("23 m2", BASE_PRICE, 23.0),
        ("25.3 m2", BASE_PRICE, 25.3),
        ("28,3 m2", BASE_PRICE, 28.3),
        ("40 metrow", BASE_PRICE, 40),
        ("40 mkw", BASE_PRICE, 40),
        ("40mkw", BASE_PRICE, 40),
        ("33 metry", BASE_PRICE, 33),
        ("2.3 m2", BASE_PRICE, None),
        ("1333 mkw", BASE_PRICE, None),
        ("2.3m2 23m2 230m2", BASE_PRICE, 23),
        ("230m2", 10000, None),
        ("20m2", 10000000, None),
    ]
)
def test_deduce_size_from_text(text, price, result):
    assert deduce_size_from_text(text=text, price=price) == result


@pytest.mark.parametrize(
    "td_str, exp_seconds", [
        ("SEKUNDę", 1),
        ("3 sekundy temu", 3),
        ("MINutę temu", MINUTE),
        ("23 minuty temu", 23 * MINUTE),
        ("Godzinę temu", HOUR),
        ("2 godziny temu", 2 * HOUR),
        ("Dzień temu", DAY),
        ("5 dni temu", 5 * DAY),
    ]
)
def test_parse_timedelta_str(td_str: str, exp_seconds: int):
    assert parse_timedelta_str_to_seconds(td_str) == exp_seconds