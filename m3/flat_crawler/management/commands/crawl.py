
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from flat_crawler.crawlers.gumtree_crawler import GumtreeCrawler
from flat_crawler.crawlers.otodom_crawler import OtodomCrawler
from flat_crawler.crawlers.base_crawler import DistrictFilter
from flat_crawler.constants import SRODMIESCIE, MOKOTOW, ZOLIBORZ, OCHOTA, BIELANY, IGNORED_DISTRICTS




class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--page-start', nargs='?', type=int, default=1)
        parser.add_argument('--page-end', nargs='?', type=int)
        parser.add_argument('--otodom', action='store_true')

    def handle(self, *args, **options):
        # for district in [SRODMIESCIE, MOKOTOW, ZOLIBORZ, OCHOTA, BIELANY]:
        if options.get('otodom'):
            OtodomCrawler(
                page_start=options.get('page_start', 1),
                page_stop=options.get('page_end', 10),
                allow_pages_without_new_posts=True,
                post_filter=DistrictFilter(ignored_districts=IGNORED_DISTRICTS),
            ).fetch_new_posts()
        else:
            GumtreeCrawler(
                district='warszawa',
                page_start=options.get('page_start', 1),
                page_stop=options.get('page_end', 10),
                allow_pages_without_new_posts=True,
                min_price=450000,
                max_price=1000000,
                post_filter=DistrictFilter(ignored_districts=IGNORED_DISTRICTS),
            ).fetch_new_posts()
