import logging
import re
import json
from io import BytesIO
from typing import Iterable, Optional, Dict, List
from datetime import datetime

import fire
from bs4 import BeautifulSoup
from PIL import Image
from dateutil import parser

from flat_crawler.models import FlatPost, Source
from flat_crawler.crawlers.base_crawler import SoupInfo, BaseCrawler

logger = logging.getLogger(__name__)


BASE_URL = 'https://www.gumtree.pl'

MIN_PRICE = 400000
MAX_PRICE = 1500000

OFFERS_TEMPLATE = ('/s-mieszkania-i-domy-sprzedam-i-kupie/%(district)s/page-%(page)d/'
                   'v1c9073l3200008p%(page)d?pr=%(min_price)d,%(max_price)d')

DISTRICT_PATTERN = r'https://www.gumtree.pl/a-mieszkania-i-domy-sprzedam-i-kupie/(.+?)/.*'


class GumtreeCrawler(BaseCrawler):
    SOURCE = Source.GUMTREE

    def __init__(
        self,
        district: str,
        min_price: int = MIN_PRICE,
        max_price: int = MAX_PRICE,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._district = district
        self._min_price = min_price
        self._max_price = max_price

    def _get_main_url(self, page_num):
        return BASE_URL + OFFERS_TEMPLATE % {
            'page': page_num,
            'min_price': self._min_price,
            'max_price': self._max_price,
            'district': self._district
        }

    def _extract_posts_from_page_soup(self, page_soup: BeautifulSoup) -> Iterable[BeautifulSoup]:
        return page_soup.findAll("div", {"class": "tileV1"})

    def _get_url(self, soup: SoupInfo) -> Optional[str]:
        return BASE_URL + soup.base.find('div', class_='title').find(
            'a', class_='href-link tile-title-text').attrs.get('href')

    def _get_heading(self, soup: SoupInfo) -> Optional[str]:
        return soup.base.find('div', class_='title').text

    def _get_district(self, soup: SoupInfo) -> Optional[str]:
        url = self._get_url(soup=soup)
        match = re.search(DISTRICT_PATTERN, url)
        if match:
            return match.group(1)
        else:
            logger.warning(f"District not found in url: {url}")

    def _get_price(self, soup: SoupInfo) -> Optional[int]:
        price_text = soup.base.find('span', class_='ad-price').text
        return int(re.sub(r'\s+', '', price_text.replace('zł', '')))

    def _get_thumbnail_url(self, soup: SoupInfo) -> Optional[str]:
        return soup.base.find('div', class_='bolt-image').find('picture').find(
            'source', {'type': 'image/jpeg'}).attrs.get('data-srcset')

    def _get_desc(self, soup: SoupInfo) -> Optional[str]:
        if soup.detailed is not None:
            return soup.detailed.find('div', class_='description').text

    def _get_size_m2(self, soup: SoupInfo) -> Optional[int]:
        SIZE_KEY = 'Wielkość (m2)'
        details_dict = self._get_details_dict(soup=soup)
        if details_dict is not None and SIZE_KEY in details_dict:
            return float(details_dict[SIZE_KEY])
        else:
            return self._deduce_size_m2_from_text(soup=soup)

    def _get_sub_district(self, soup: SoupInfo) -> Optional[str]:
        # TODO Implement
        return None

    def _get_street(self, soup: SoupInfo) -> Optional[str]:
        # TODO Implement
        return None

    def _get_img_urls(self, soup: SoupInfo) -> Optional[List[str]]:
        if soup.detailed is not None:
            return list(filter(lambda x: x is not None, [
                image.attrs.get('src')
                for image in soup.detailed.find('div', class_='vip-gallery').findAll('img')
            ]))

    def _get_details_dict(self, soup: SoupInfo) -> Optional[Dict]:
        if soup.detailed is not None:
            details_dict = {}
            for entry in soup.detailed.find('ul', class_='selMenu').findAll('li'):
                name = entry.find('span', class_='name')
                val = entry.find('span', class_='value')
                if name and val:
                    details_dict[name.text] = val.text
            return details_dict

    def _get_info_dict_json(self, soup: SoupInfo) -> Optional[str]:
        details_dict = self._get_details_dict(soup=soup)
        if details_dict is not None:
            return json.dumps(details_dict)

    def _get_dt_posted(self, soup: SoupInfo) -> Optional[datetime]:
        DT_KEY = 'Data dodania'
        details_dict = self._get_details_dict(soup=soup)
        if details_dict is None:
            return None

        if DT_KEY in details_dict:
            return parser.parse(details_dict[DT_KEY], dayfirst=True)
        else:
            logger.warning(
                f"GUMTREE: didn't found date added, available fields: {details_dict.keys()}"
            )
