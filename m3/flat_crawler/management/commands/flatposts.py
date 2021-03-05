
from django.core.management.base import BaseCommand, CommandError

from flat_crawler.management.commands.crawl import Command as Crawl
from flat_crawler.management.commands.extract_info import Command as ExtractInfo
from flat_crawler.management.commands.match_posts import Command as MatchPosts


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--lookback-days', nargs='?', type=int)
        parser.add_argument('--page-start', nargs='?', type=int)
        parser.add_argument('--page-stop', nargs='?', type=int)
        parser.add_argument('--preview', action='store_true')

    def handle(self, *args, **options):
        crawl_params = {}
        preview_mode = options.pop('preview')
        if preview_mode:
            for key in options.keys():
                options[key] = 1

        Crawl().handle(otodom=True, **options)
        Crawl().handle(**options)

        if not preview_mode:
            ExtractInfo.handle(locations=True)
            ExtractInfo.handle(geodata=True)
            ExtractInfo.handle(parse_geodata=True)
            ExtractInfo.handle(attach_areas=True)
        ExtractInfo.handle()
        MatchPosts.handle()
