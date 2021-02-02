
import re
import json
import logging
from typing import List, Optional
from io import BytesIO

import requests
from PIL import Image
from bs4 import BeautifulSoup

from flat_crawler.constants import THUMBNAIL_SIZE
from flat_crawler import exceptions

logger = logging.getLogger(__name__)

IMG_BYTES_DELIM = b'$!%'


def get_img_from_url(img_url, resize=THUMBNAIL_SIZE):
    try:
        img = Image.open(BytesIO(requests.get(img_url).content))
        if resize:
            img = img.resize(resize, Image.ANTIALIAS)
        return img
    except Exception as exc:
        logger.warning(f"Image failed to load from {img_url}")
        raise exceptions.URLFailedToLoadException(exc)


def get_img_bytes_from_url(img_url: str, resize=THUMBNAIL_SIZE) -> bytes:
    img = get_img_from_url(img_url=img_url, resize=resize)
    img_bytes = BytesIO()
    img.save(img_bytes, format="JPEG", optimize=True, quality=40)
    return img_bytes.getvalue()


def img_urls_to_bytes(img_urls: List[str]) -> Optional[bytes]:
    img_bytes_list = []
    for img_url in img_urls:
        try:
            img_bytes = get_img_bytes_from_url(img_url=img_url)
            img_bytes_list.append(img_bytes)
        except exceptions.URLFailedToLoadException as exc:
            logger.warning(f"loading image from {img_url} failed, do not add to img bytes.")
    if img_bytes_list:
        return IMG_BYTES_DELIM.join(img_bytes_list)


def bytes_to_images(img_list_bytes: Optional[bytes]) -> List:
    if img_list_bytes is None:
        return []
    return [Image.open(BytesIO(bts)) for bts in img_list_bytes.split(IMG_BYTES_DELIM)]
