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


MIN_PRICE = 400000
MAX_PRICE = 1500000

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
    '&locations%5B0%5D%5Bdistrict_id%5D=39' # Mokotów
    '&locations%5B1%5D%5Bregion_id%5D=7'
    '&locations%5B1%5D%5Bsubregion_id%5D=197'
    '&locations%5B1%5D%5Bcity_id%5D=26'
    '&locations%5B1%5D%5Bdistrict_id%5D=300420' # Stary Żoliborz
    '&locations%5B2%5D%5Bregion_id%5D=7'
    '&locations%5B2%5D%5Bsubregion_id%5D=197'
    '&locations%5B2%5D%5Bcity_id%5D=26'
    '&locations%5B2%5D%5Bdistrict_id%5D=961' # Muranów
    '&locations%5B3%5D%5Bregion_id%5D=7'
    '&locations%5B3%5D%5Bsubregion_id%5D=197'
    '&locations%5B3%5D%5Bcity_id%5D=26'
    '&locations%5B3%5D%5Bdistrict_id%5D=44' # Śródmieście
    '&locations%5B3%5D%5Bregion_id%5D=7'
    '&locations%5B3%5D%5Bsubregion_id%5D=197'
    '&locations%5B3%5D%5Bcity_id%5D=26'
    '&locations%5B3%5D%5Bdistrict_id%5D=38' # Bielany
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
    SOURCE = Source.OTODOM

    def __init__(
        self,
        district: str,
        min_price: int=MIN_PRICE,
        max_price: int=MAX_PRICE,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._district = district
        self._min_price = min_price
        self._max_price = max_price

    def _get_main_url(self, page_num):
        """ Return search page url for given page number. """
        return OTODOM_SEARCH_URL % {'page_num': page_num}

    def _extract_posts_from_page_soup(self, page_soup: BeautifulSoup) -> Iterable[BeautifulSoup]:
        """ Return list of page soups for each offer on the search page. """
        return page_soup.findAll("article", {"class":"offer-item"})

    def _get_url(self, soup: SoupInfo) -> Optional[str]:
        """ Get url of details page of a given offer. """
        return soup.get('data-url')

    def _get_heading(self, soup: SoupInfo) -> Optional[str]:
        """ Get title of offer. """
        return soup.find('span', {'class':'offer-item-title'}).text

    def _get_district(self, soup: SoupInfo) -> Optional[str]:
        location = re.search('Warszawa.+', soup.header.p.text)
        return location.group().split()[1]

    def _get_price(self, soup: SoupInfo) -> Optional[int]:
        price = soup.find('li', {'class':'offer-item-price'}).text
        return int(price.strip().replace('zł','').replace(' ', ''))

    def _get_thumbnail_url(self, soup: SoupInfo) -> Optional[str]:
        """ Url of thumbnail image next to offer title. """
        return soup.figure.a.get('href')

    def _get_desc(self, soup: SoupInfo) -> Optional[str]:
        """ Full description of offer. """
        # available description only on detailed flat page
        return None

    def _get_size_m2(self, soup: SoupInfo) -> Optional[int]:
        return int(soup.find('li', {'class':'offer-item-area'}).text.split()[0])

    def _get_sub_district(self, soup: SoupInfo) -> Optional[str]:
        sub_district = self._get_district.location.group().split()
        if len(sub_district) > 2:
            return sub_district[2]
        else:
            return None

    def _get_street(self, soup: SoupInfo) -> Optional[str]:
        # TODO Implement
        return None

    def _get_img_urls(self, soup: SoupInfo) -> Optional[List[str]]:
        """ Get urls of images on post details page. """
        #TODO - very deep nested thumbnails 
        return None

    def _get_details_dict(self, soup: SoupInfo) -> Optional[Dict]:
        if soup.detailed is not None:
            details_dict = {}
            # TODO
            #return details_dict

    def _get_info_dict_json(self, soup: SoupInfo) -> Optional[str]:
        """ Dump to json dictionary any additional information that doesn't fit into models fields.
        """
        # details_dict: Dict = get_some_details_dict
        # return json.dumps(details_dict)
        return None

    def _get_dt_posted(self, soup: SoupInfo) -> Optional[datetime]:
        """ Get datetime of moment when the post was added. """
        return None
