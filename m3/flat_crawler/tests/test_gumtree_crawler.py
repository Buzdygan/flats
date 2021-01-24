from datetime import datetime
from io import BytesIO
from unittest.mock import patch

import pytest
from PIL import Image
from bs4 import BeautifulSoup

from flat_crawler.models import FlatPost, PostHash
from flat_crawler.crawlers.gumtree_crawler import GumtreeCrawler

#pylint:disable=no-member

URL_TO_PAGE = {
    "main": 'static/gumtree_page.html',
    "detail": 'static/gumtree_detail_page.html',
}
IMG_BYTES = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x04\x00\x00\x00\x02\x08\x02\x00\x00\x00\xf0\xca\xea4\x00\x00\x00#IDATx\x9cc\xec\xcd\x0bcgg\x15\x97S\xfe\xfe\xf1\x1d\xd3\xf37\xef\xfer\x8b\xfegb~\xf1\xfc)\x00\x85\xf4\x0c,c1A\xca\x00\x00\x00\x00IEND\xaeB`\x82'


def mock_get_img_from_url(img_url, resize=None):
    img = Image.open(BytesIO(IMG_BYTES))
    if resize:
        img = img.resize(resize)
    return img


class TestGumtreeCrawler(GumtreeCrawler):

    def _get_post_pages_to_crawl(self, page_start=1, page_stop=100):
        return ["main"]

    def _get_soup_from_url(self, url: str):
        with open(URL_TO_PAGE[url], 'rb') as reader:
            return BeautifulSoup(reader.read(), 'html.parser')

    def _post_from_soup(self, soup: BeautifulSoup):
        post = super()._post_from_soup(soup=soup)
        post.url = "detail"
        return post


@patch('flat_crawler.crawlers.helpers.get_img_from_url', new=mock_get_img_from_url)
@pytest.mark.django_db
def test_gumtree_crawler():
    crawler = TestGumtreeCrawler(start_dt=datetime(2000, 1, 1))
    crawler.fetch_new_posts()

    assert FlatPost.objects.count() == 23
    assert PostHash.objects.count() == 23

    assert FlatPost.objects.order_by('price').first().price == 453000
    assert FlatPost.objects.order_by('price').last().price == 1000000
