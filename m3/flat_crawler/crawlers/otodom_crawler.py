import logging
import re
import json
from typing import Iterable, Optional, Dict, List
from datetime import datetime

from bs4 import BeautifulSoup
from dateutil import parser

from flat_crawler.models import Source
from flat_crawler.crawlers.base_crawler import SoupInfo, BaseCrawler

logger = logging.getLogger(__name__)

OTODOM_SEARCH_URL = (
    'otodom.pl/sprzedaz/mieszkanie/'
    '?search%5Bfilter_float_price%3Afrom%5D=400000'
    '&search%5Bfilter_float_price%3Ato%5D=1300000'
    '&search%5Bfilter_float_m%3Afrom%5D=40'
    '&search%5Bfilter_float_m%3Ato%5D=90'
    '&search%5Bfilter_enum_market%5D=secondary'
    '&search%5Bfilter_float_building_floors_num%3Ato%5D=8'
    '&search%5Bfilter_float_build_year%3Ato%5D=1960'
    '&locations%5B0%5D%5Bregion_id%5D=7'
    '&locations%5B0%5D%5Bsubregion_id%5D=197'
    '&locations%5B0%5D%5Bcity_id%5D=26'
    '&locations%5B0%5D%5Bdistrict_id%5D=39'
    '&locations%5B1%5D%5Bregion_id%5D=7'
    '&locations%5B1%5D%5Bsubregion_id%5D=197'
    '&locations%5B1%5D%5Bcity_id%5D=26'
    '&locations%5B1%5D%5Bdistrict_id%5D=300420'
    '&locations%5B2%5D%5Bregion_id%5D=7'
    '&locations%5B2%5D%5Bsubregion_id%5D=197'
    '&locations%5B2%5D%5Bcity_id%5D=26'
    '&locations%5B2%5D%5Bdistrict_id%5D=961'
    '&locations%5B3%5D%5Bregion_id%5D=7'
    '&locations%5B3%5D%5Bsubregion_id%5D=197'
    '&locations%5B3%5D%5Bcity_id%5D=26'
    '&locations%5B3%5D%5Bdistrict_id%5D=44'
    '&page=%(page_num)d'
)

"""
UWAGI:

Otodom ma dość uporządkowaną strukturę i mozna wyciagnąć wiele przydatnych informacji.
Wszystko co nie pasuje do pól modelu, mozna dodac do slownika w metodzie _get_info_dict_json
Najlepiej przeniesc tam wszystkie dane z tabelki "Szczegóły ogłoszenia", jako nazwa pola: wartość.

Dzielnicę mozna ustawić sobie w bazowym urlu (OTODOM_SEARCH_URL), w tym momencie jest ustawiona
na czterny główne dzielnice, najlepiej chyba będzie to wyszukiwać dzielnica po dzielnicy.

W szczegolnosci lokalizacja na stronie szczegolow danej oferty, tam często jest nazwa ulicy.

bazowy url w jednym wierszu:
https://www.otodom.pl/sprzedaz/mieszkanie/?search%5Bfilter_float_price%3Afrom%5D=400000&search%5Bfilter_float_price%3Ato%5D=1300000&search%5Bfilter_float_m%3Afrom%5D=40&search%5Bfilter_float_m%3Ato%5D=90&search%5Bfilter_enum_market%5D=secondary&search%5Bfilter_float_building_floors_num%3Ato%5D=8&search%5Bfilter_float_build_year%3Ato%5D=1960&locations%5B0%5D%5Bregion_id%5D=7&locations%5B0%5D%5Bsubregion_id%5D=197&locations%5B0%5D%5Bcity_id%5D=26&locations%5B0%5D%5Bdistrict_id%5D=39&locations%5B1%5D%5Bregion_id%5D=7&locations%5B1%5D%5Bsubregion_id%5D=197&locations%5B1%5D%5Bcity_id%5D=26&locations%5B1%5D%5Bdistrict_id%5D=300420&locations%5B2%5D%5Bregion_id%5D=7&locations%5B2%5D%5Bsubregion_id%5D=197&locations%5B2%5D%5Bcity_id%5D=26&locations%5B2%5D%5Bdistrict_id%5D=961&locations%5B3%5D%5Bregion_id%5D=7&locations%5B3%5D%5Bsubregion_id%5D=197&locations%5B3%5D%5Bcity_id%5D=26&locations%5B3%5D%5Bdistrict_id%5D=44&page=2
"""


class OtodomCrawler(BaseCrawler):
    SOURCE = Source.GUMTREE

    def __init__(
        **kwargs
    ):
        super().__init__(**kwargs)

    def _get_main_url(self, page_num):
        """ Return search page url for given page number. """
        return OTODOM_SEARCH_URL % {'page_num': page_num}

    def _extract_posts_from_page_soup(self, page_soup: BeautifulSoup) -> Iterable[BeautifulSoup]:
        """ Return list of page soups for each offer on the search page. """
        raise NotImplementedError

    def _get_url(self, soup: SoupInfo) -> Optional[str]:
        """ Get url of details page of a given offer. """
        return None

    def _get_heading(self, soup: SoupInfo) -> Optional[str]:
        """ Get title of offer. """
        return None

    def _get_district(self, soup: SoupInfo) -> Optional[str]:
        return None

    def _get_price(self, soup: SoupInfo) -> Optional[int]:
        return None

    def _get_thumbnail_url(self, soup: SoupInfo) -> Optional[str]:
        """ Url of thumbnail image next to offer title. """
        return None

    def _get_desc(self, soup: SoupInfo) -> Optional[str]:
        """ Full description of offer. """
        return None

    def _get_size_m2(self, soup: SoupInfo) -> Optional[int]:
        return None

    def _get_sub_district(self, soup: SoupInfo) -> Optional[str]:
        # TODO Implement
        return None

    def _get_street(self, soup: SoupInfo) -> Optional[str]:
        # TODO Implement
        return None

    def _get_img_urls(self, soup: SoupInfo) -> Optional[List[str]]:
        """ Get urls of images on post details page. """
        return None

    def _get_info_dict_json(self, soup: SoupInfo) -> Optional[str]:
        """ Dump to json dictionary any additional information that doesn't fit into models fields.
        """
        # details_dict: Dict = get_some_details_dict
        # return json.dumps(details_dict)
        return None

    def _get_dt_posted(self, soup: SoupInfo) -> Optional[datetime]:
        """ Get datetime of moment when the post was added. """
        return None
