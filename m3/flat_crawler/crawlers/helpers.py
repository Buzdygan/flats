
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
    logger.info(f"Fetching soup from url {url}")
    try:
        page = requests.get(url)
        return BeautifulSoup(page.content, "html.parser")
    except Exception as exc:
        logger.error(f"Failed to load url: {url}")
        raise exceptions.URLFailedToLoadException(exc)


def get_img_from_url(img_url, resize=None):
    logger.info(f"Fetching image from url {img_url}")
    img = Image.open(BytesIO(requests.get(img_url).content))
    if resize:
        img = img.resize(resize)
    return img
