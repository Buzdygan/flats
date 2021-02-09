
import pytest
from django.test import TestCase


from flat_crawler.utils.text_utils import deduce_size_from_text


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
