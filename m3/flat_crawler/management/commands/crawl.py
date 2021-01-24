
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from flat_crawler.crawlers.gumtree_crawler import GumtreeCrawler




class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        GumtreeCrawler(start_dt=datetime(2020, 1, 1), pages_limit=2).fetch_new_posts()
