from datetime import datetime
from io import BytesIO
from unittest.mock import patch

import pytest
from PIL import Image
from bs4 import BeautifulSoup

from flat_crawler.models import FlatPost, PostHash
from flat_crawler.crawlers.otodom_crawler import OtodomCrawler

#pylint:disable=no-member

MAIN_URL = "main"
DETAIL_URL = "detail_url"

URL_TO_PAGE = {
    MAIN_URL: 'static/otodom_page.html',
    DETAIL_URL: 'static/otodom_detail_page.html',
}
IMG_BYTES = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x04\x00\x00\x00\x02\x08\x02\x00\x00\x00\xf0\xca\xea4\x00\x00\x00#IDATx\x9cc\xec\xcd\x0bcgg\x15\x97S\xfe\xfe\xf1\x1d\xd3\xf37\xef\xfer\x8b\xfegb~\xf1\xfc)\x00\x85\xf4\x0c,c1A\xca\x00\x00\x00\x00IEND\xaeB`\x82'


def mock_get_img_from_url(img_url, resize=None):
    img = Image.open(BytesIO(IMG_BYTES))
    if resize:
        img = img.resize(resize)
    return img

def mock_get_soup_from_url(url: str):
    with open(URL_TO_PAGE[url], 'rb') as reader:
        return BeautifulSoup(reader.read(), 'html.parser')


class TestOtodomCrawler(OtodomCrawler):

    def _get_post_pages_to_crawl(self, page_start=1, page_stop=1):
        return [MAIN_URL]

    def _get_url(self, soup):
        return DETAIL_URL


@patch('flat_crawler.utils.img_utils.get_img_from_url', new=mock_get_img_from_url)
@patch('flat_crawler.crawlers.base_crawler.get_soup_from_url', new=mock_get_soup_from_url)
@pytest.mark.django_db
def test_otodom_crawler():
    crawler = TestOtodomCrawler()
    crawler.fetch_new_posts()

    assert FlatPost.objects.count() == 27
    assert PostHash.objects.count() == 27

    assert FlatPost.objects.order_by('price').first().price == 609000
    assert FlatPost.objects.order_by('price').last().price == 799900

    for post in FlatPost.objects.all():
        assert post.price
        assert post.heading
        assert post.dt_posted
        assert post.size_m2
        assert post.street == 'Puławska 16'

    districts = sorted(set(FlatPost.objects.values_list('district', flat=True)))
    assert districts == ['mokotow', 'ochota', 'srodmiescie', 'ursus', 'wola', 'zoliborz']
    sub_districts = sorted(
        set(x for x in FlatPost.objects.values_list('sub_district', flat=True) if x))
    assert sub_districts == ['gorny', 'muranow', 'stare', 'stary']
