

from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from flat_crawler.crawlers.gumtree_crawler import GumtreeCrawler
from flat_crawler.crawlers.otodom_crawler import OtodomCrawler
from flat_crawler.crawlers.base_crawler import DistrictFilter
from flat_crawler import constants as ct


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--lookback-days', nargs='?', type=int)
        parser.add_argument('--page-start', nargs='?', type=int)
        parser.add_argument('--page-stop', nargs='?', type=int)
        parser.add_argument('--otodom', action='store_true')

    def handle(self, *args, **options):
        # for district in [SRODMIESCIE, MOKOTOW, ZOLIBORZ, OCHOTA, BIELANY]:
        crawler_params = {
            'min_price': ct.MIN_PRICE,
            'max_price': ct.MAX_PRICE,
            'post_filter': DistrictFilter(ignored_districts=ct.IGNORED_DISTRICTS),
        }
        for key in ['page_start', 'page_stop', 'lookback_days']:
            if key in options and options[key] is not None:
                crawler_params[key] = options[key]

        if options.get('otodom'):
            OtodomCrawler(
                **crawler_params,
            ).fetch_new_posts()
        else:
            for district in ct.SELECTED_DISTRICTS:
                GumtreeCrawler(
                    **crawler_params,
                    district=district,
                ).fetch_new_posts()
