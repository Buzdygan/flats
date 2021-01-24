
import re
from io import BytesIO
from typing import Iterable

import requests
from bs4 import BeautifulSoup
from PIL import Image

from flat_crawler.models import FlatPost, Source
from flat_crawler.crawlers.base_crawler import BaseCrawler, get_img_and_bytes_from_url

BASE_URL = 'https://www.gumtree.pl'

MIN_PRICE = 450000
MAX_PRICE = 1500000

OFFERS_TEMPLATE = ('/s-mieszkania-i-domy-sprzedam-i-kupie/warszawa/page-%(page)d/'
                   'v1c9073l3200008p%(page)d?pr=%(min_price)d,%(max_price)d')

class GumtreeCrawler(BaseCrawler):
    SOURCE = Source.GUMTREE

    def _get_post_pages_to_crawl(self, max_pages):
        return [
            BASE_URL + OFFERS_TEMPLATE % {
                'page': page, 'min_price': MIN_PRICE, 'max_price': MAX_PRICE}
            for page in range(1, max_pages + 1)
        ]

    def _post_from_soup(self, soup: BeautifulSoup) -> FlatPost:
        post = FlatPost()

        post.heading = soup.find('div', class_='title').text
        post.url = BASE_URL + soup.find('div', class_='title').find(
            'a', class_='href-link tile-title-text').attrs.get('href')
        post.desc = soup.find('div', class_='description').text

        price_text = soup.find('span', class_='ad-price').text
        post.price = int(re.sub(r'\s+', '', price_text.replace('zł', '')))

        img_url = soup.find('div', class_='bolt-image').find('picture').find(
            'source', {'type': 'image/jpeg'}).attrs.get('data-srcset')

        self._add_thumbnail(post=post, img_url=img_url)

    def _add_details(self, post: FlatPost, details_soup: BeautifulSoup) -> None:
        post.desc = details_soup.find('div', class_='description').text
        details_dict = {}
        for entry in details_soup.find('ul', class_='selMenu').findAll('li'):
            name = entry.find('span', class_='name')
            val = entry.find('span', class_='value')
            if name and val:
                details_dict[name.text] = val.text

    def _extract_posts_from_page_soup(self, page_soup: BeautifulSoup) -> Iterable[BeautifulSoup]:
        return page_soup.findAll("div", {"class": "tileV1"})
