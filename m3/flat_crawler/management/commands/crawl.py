
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from flat_crawler.crawlers.gumtree_crawler import GumtreeCrawler
from flat_crawler.crawlers.base_crawler import DistrictFilter
from flat_crawler.constants import SRODMIESCIE, MOKOTOW, ZOLIBORZ, OCHOTA, BIELANY, IGNORED_DISTRICTS




class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # for district in [SRODMIESCIE, MOKOTOW, ZOLIBORZ, OCHOTA, BIELANY]:
        for district in ['warszawa']:
            GumtreeCrawler(
                district=district,
                start_dt=datetime(2020, 1, 1),
                page_start=8,
                page_stop=18,
                allow_pages_without_new_posts=True,
                min_price=450000,
                max_price=1000000,
                post_filter=DistrictFilter(ignored_districts=IGNORED_DISTRICTS),
            ).fetch_new_posts()
