from django.core.management.base import BaseCommand, CommandError

from flat_crawler.utils.flat_post_matcher import MatchingEngine


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        MatchingEngine().match_posts()
