import logging
import re
import json
from typing import Iterable, Optional, Dict, List
from datetime import datetime

from bs4 import BeautifulSoup
from dateutil import parser

from flat_crawler.models import Source
from flat_crawler.crawlers.base_crawler import SoupInfo
from flat_crawler.crawlers.timeless_crawler import TimelessCrawler
from flat_crawler.utils.text_utils import normalize_word
from flat_crawler import constants as ct

logger = logging.getLogger(__name__)


OTODOM_SEARCH_URL = (
    'https://www.otodom.pl/sprzedaz/mieszkanie/'
    '?search%5Bfilter_float_price%3Afrom%5D=200000'
    '&search%5Bfilter_float_price%3Ato%5D=500000'
    '&search%5Bfilter_float_m%3Afrom%5D=30'
    '&search%5Bfilter_float_m%3Ato%5D=50'
    '&locations%5B0%5D%5Bregion_id%5D=7'
    '&locations%5B0%5D%5Bsubregion_id%5D=197'
    '&locations%5B0%5D%5Bcity_id%5D=26'
    '&locations%5B0%5D%5Bdistrict_id%5D=39'
    '&locations%5B1%5D%5Bregion_id%5D=7'
    '&locations%5B1%5D%5Bsubregion_id%5D=197'
    '&locations%5B1%5D%5Bcity_id%5D=26'
    '&locations%5B1%5D%5Bdistrict_id%5D=44'
    '&locations%5B2%5D%5Bregion_id%5D=7'
    '&locations%5B2%5D%5Bsubregion_id%5D=197'
    '&locations%5B2%5D%5Bcity_id%5D=26'
    '&locations%5B2%5D%5Bdistrict_id%5D=53'
    '&locations%5B3%5D%5Bregion_id%5D=7'
    '&locations%5B3%5D%5Bsubregion_id%5D=197'
    '&locations%5B3%5D%5Bcity_id%5D=26'
    '&locations%5B3%5D%5Bdistrict_id%5D=300426'
    '&locations%5B4%5D%5Bregion_id%5D=7'
    '&locations%5B4%5D%5Bsubregion_id%5D=197'
    '&locations%5B4%5D%5Bcity_id%5D=26'
    '&locations%5B4%5D%5Bdistrict_id%5D=117'
    '&page={page_num}'
)

DEFAULT_PAGE_STOP = 50

class OtodomCrawler(TimelessCrawler):
    SOURCE = Source.OTODOM

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._dt_now = datetime.now()
        self._field_getters_dict['street'] = self._get_street
        self._field_getters_dict['sub_district'] = self._get_sub_district

    def _get_main_url(self, page_num):
        """ Return search page url for given page number. """
        return OTODOM_SEARCH_URL.format(page_num=page_num)

    def _extract_posts_from_page_soup(self, page_soup: BeautifulSoup) -> Iterable[BeautifulSoup]:
        """ Return list of page soups for each offer on the search page. """
        return page_soup.findAll("article", {"class":"offer-item"})

    def _get_url(self, soup: SoupInfo) -> Optional[str]:
        """ Get url of details page of a given offer. """
        return soup.base.get('data-url')

    def _get_heading(self, soup: SoupInfo) -> Optional[str]:
        """ Get a title of offer. """
        return soup.base.find('span', {'class':'offer-item-title'}).text

    def _get_locations(self, soup: SoupInfo) -> List[str]:
        location = re.search('Warszawa.+', soup.base.header.p.text)
        return location.group().split()

    def _get_district(self, soup: SoupInfo) -> Optional[str]:
        """Get an offer's district name."""
        return normalize_word(self._get_locations(soup=soup)[1])

    def _get_price(self, soup: SoupInfo) -> Optional[int]:
        """Get a price of the offer."""
        price = soup.base.find('li', {'class':'offer-item-price'}).text
        return int(price.strip().replace('zł','').replace(' ', ''))

    def _get_thumbnail_url(self, soup: SoupInfo) -> Optional[str]:
        """Get url of thumbnail image next to offer title. """
        return soup.base.a.span.get('data-src')

    def _get_desc(self, soup: SoupInfo) -> Optional[str]:
        """ Return full description of the offer's apartment. """
        if soup.detailed is not None:
            description_tag = soup.detailed.div.find('section', {'role':'region'}).find_all('p')
            description = ''
            for elm in description_tag:
                description += elm.text
            return description

    def _get_size_m2(self, soup: SoupInfo) -> Optional[float]:
        """Return the size of the offer's apartment."""
        size_str = soup.base.find('li', {'class':'offer-item-area'}).text.split()[0]
        size_str = size_str.replace(',', '.')
        return float(size_str)

    def _get_sub_district(self, soup: SoupInfo) -> Optional[str]:
        """Get name of the subdistrict for the offer if available."""
        locations = self._get_locations(soup=soup)
        if len(locations) > 2:
            return normalize_word(locations[2])

    def _get_street(self, soup: SoupInfo) -> Optional[str]:
        """Return the street name -if available - of the object."""
        # We have a separate post processing command that tries to extract street from heading/text
        # heading_search = re.search('ul.', self._get_heading(soup))
        # if heading_search:
        #     start = heading_search.span()[0]
        #     return self._get_heading(soup)[start:]

        if soup.detailed is not None:
            map_localisation = soup.detailed.find('a', {'href': '#map'})
            if map_localisation:
                loc_elements = map_localisation.text.split(',')
                for elm in loc_elements:
                    if 'ul.' in elm:
                        return elm.strip()
                return loc_elements[-1].strip()

    def _get_img_urls(self, soup: SoupInfo) -> Optional[List[str]]:
        """ Get urls of images on post details page. """
        images = eval(soup.base.figure.get('data-quick-gallery'))
        urls = [image['photo'].replace('\\/','/') for image in images]
        return urls

    def _get_details_dict(self, soup: SoupInfo) -> Optional[Dict]:
        """Return all details which are available for the offer.""" 
        details_dict = {}
        if soup.detailed is not None:
            details_list = soup.detailed.div.find_all('div', {'role':'region'})
            for detail in details:
                detail = detail.text.split(':')
                details_dict[detail[0]] = detail[1]
        add_info = self._additional_info(soup=soup)
        details_dict.update(add_info)
        return details_dict

    def _additional_info(self, soup: SoupInfo):
        """Get additional info apart from description part."""
        new_dict = {}
        if soup.detailed is not None:
            additional_info = soup.detailed.find('div', class_='ad.ad-features.categorized-list').find_all('div')
            if additional_info is not None:
                for elm in additional_info:
                    category = elm.h3.text
                    cat_values = elm.ul.find_all('li')
                    new_dict[category] = cat_values
        return new_dict

    def _get_info_dict_json(self, soup: SoupInfo) -> Optional[str]:
        """ Dump to json dictionary any additional information that doesn't fit into models fields.
        """
        details_dict: Dict = self._get_details_dict(soup=soup)
        if details_dict is not None:
            return json.dumps(details_dict)
        else:
            return None

    def _get_dt_posted(self, soup: SoupInfo) -> Optional[datetime]:
        """ Get datetime of moment when the post was added. """
        # not available at OTODOM service
        return self._dt_now
