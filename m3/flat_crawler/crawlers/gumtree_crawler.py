import logging
import re
from io import BytesIO
from typing import Iterable
from datetime import datetime

import requests
import fire
from bs4 import BeautifulSoup
from PIL import Image
from dateutil import parser

from flat_crawler.models import FlatPost, Source
from flat_crawler.crawlers.base_crawler import BaseCrawler, get_img_and_bytes_from_url
from flat_crawler.crawlers.helpers import deduce_size_from_text, get_photo_signature


BASE_URL = 'https://www.gumtree.pl'

MIN_PRICE = 450000
MAX_PRICE = 1500000

OFFERS_TEMPLATE = ('/s-mieszkania-i-domy-sprzedam-i-kupie/warszawa/page-%(page)d/'
                   'v1c9073l3200008p%(page)d?pr=%(min_price)d,%(max_price)d')

class GumtreeCrawler(BaseCrawler):
    SOURCE = Source.GUMTREE

    def _get_post_pages_to_crawl(self, page_start=1, page_stop=100):
        return [
            BASE_URL + OFFERS_TEMPLATE % {
                'page': page, 'min_price': MIN_PRICE, 'max_price': MAX_PRICE}
            for page in range(page_start, page_stop + 1)
        ]

    def _post_from_soup(self, soup: BeautifulSoup) -> FlatPost:
        post = FlatPost()

        # title
        post.heading = soup.find('div', class_='title').text

        # url
        post.url = BASE_URL + soup.find('div', class_='title').find(
            'a', class_='href-link tile-title-text').attrs.get('href')

        # short description
        post.desc = soup.find('div', class_='description').text

        # price
        price_text = soup.find('span', class_='ad-price').text
        post.price = int(re.sub(r'\s+', '', price_text.replace('zł', '')))

        # thumbnail
        img_url = soup.find('div', class_='bolt-image').find('picture').find(
            'source', {'type': 'image/jpeg'}).attrs.get('data-srcset')
        self._add_thumbnail(post=post, img_url=img_url)

        return post

    def _add_details(self, post: FlatPost, details_soup: BeautifulSoup) -> None:
        # description
        post.desc = details_soup.find('div', class_='description').text

        # getting details dict
        details_dict = {}
        for entry in details_soup.find('ul', class_='selMenu').findAll('li'):
            name = entry.find('span', class_='name')
            val = entry.find('span', class_='value')
            if name and val:
                details_dict[name.text] = val.text

        # size
        size = details_dict.get('Wielkość (m2)')
        if size is not None:
            post.size_m2 = float(size)
        else:
            text = post.heading + ' ' + post.desc
            post.size_m2 = deduce_size_from_text(text=text, price=post.price) #pylint:disable=assignment-from-none

        if post.size_m2 is None:
            logging.warning(f"Couldn't get size for {post}")

        # date added
        date_added = details_dict.get('Data dodania')
        if date_added:
            post.dt_posted = parser.parse(date_added)
        else:
            logging.warning(
                f"GUMTREE: didn't found date added, available fields: {details_dict.keys()}"
                f" In post: {post}."
            )

        # images
        image_urls = list(filter(lambda x: x is not None, [
            image.attrs.get('src')
            for image in details_soup.find('div', class_='vip-gallery').findAll('img')
        ]))
        post.photos_signature_json = get_photo_signature(image_urls=image_urls)


    def _extract_posts_from_page_soup(self, page_soup: BeautifulSoup) -> Iterable[BeautifulSoup]:
        return page_soup.findAll("div", {"class": "tileV1"})
