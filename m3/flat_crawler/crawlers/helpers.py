
import re
import json
import logging
from io import BytesIO

import requests
from PIL import Image
from bs4 import BeautifulSoup

from flat_crawler.constants import MINATURE_SIZE
from flat_crawler import exceptions

logger = logging.getLogger(__name__)


def get_soup_from_url(url: str):
    try:
        page = requests.get(url)
        return BeautifulSoup(page.content, "html.parser")
    except Exception as exc:
        logger.error(f"Failed to load url: {url}")
        raise exceptions.URLFailedToLoadException(exc)


def get_img_from_url(img_url, resize=None):
    img = Image.open(BytesIO(requests.get(img_url).content))
    if resize:
        img = img.resize(resize)
    return img


def get_img_and_bytes_from_url(img_url: str, resize=None):
    img = get_img_from_url(img_url=img_url)
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    return img, img_bytes


def get_photo_signature(image_urls):
    return json.dumps([list(get_img_from_url(img_url=img_url, resize=MINATURE_SIZE).getdata())
                       for img_url in image_urls])


MIN_SIZE = 10
MAX_SIZE = 1000
MIN_PRICE_PER_M = 3000
MAX_PRICE_PER_M = 30000
AVG_PRICE_PER_M = 11000


def deduce_size_from_text(text: str, price: int):
    regexp = r"[+-]? *((?:\d+(?:\.\d*)?|\.\d+|)(?:[eE][+-]?\d+)?|(?:\d+(?:\,\d*)?|\,\d+|)(?:[eE][+-]?\d+)?)\s*(m2|metrów|metrow|metry|m kw|m.kw.|m kw.|m. kw|mkw)"

    unit_pattern = re.compile(regexp, re.IGNORECASE)
    found = re.findall(unit_pattern, text)
    if not found:
        return

    floats = []
    for float_str, _ in found:
        float_str = float_str.replace(',', '.')
        try:
            floats.append(float(float_str))
        except Exception:
            pass
    sizes = [size for size in floats if MIN_SIZE <= size <= MAX_SIZE]
    sizes = [size for size in floats
             if MIN_PRICE_PER_M <= price / size <= MAX_PRICE_PER_M]

    if sizes:
        return min(sizes, key=lambda size: abs(price / size - AVG_PRICE_PER_M))
