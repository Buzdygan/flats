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


class Crawler(BaseCrawler):
    SOURCE = Source.GUMTREE

    def __init__(
        **kwargs
    ):
        super().__init__(**kwargs)

    def _get_main_url(self, page_num):
        """ Return search page url for given page number. """
        raise NotImplementedError

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
