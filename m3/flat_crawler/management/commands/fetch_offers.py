
from django.core.management.base import BaseCommand, CommandError

from flat_crawler.management.commands.crawl import Command as Crawl
from flat_crawler.management.commands.extract_info import Command as ExtractInfo
from flat_crawler.management.commands.match_posts import Command as MatchPosts


class Command(BaseCommand):
    def handle(self, *args, **options):
        args = {
            'lookback_days': 1,
        }
        Crawl().handle(**args)
        Crawl().handle(otodom=True, **args)
        MatchPosts().handle()