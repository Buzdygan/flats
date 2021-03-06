from django.core.management.base import BaseCommand, CommandError

from flat_crawler.utils.flat_post_matcher import MatchingEngine
from flat_crawler.models import Flat, FlatPost, ImageMatch


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-matching', action='store_true', help='Remove all matching data',
        )

    def handle(self, *args, **options):
        if options.get('reset_matching'):
            self._reset_matching()
        else:
            MatchingEngine().match_posts()

    def _reset_matching(self):
        Flat.objects.all().delete()
        ImageMatch.objects.all().delete()
        for post in FlatPost.objects.all():
            post.is_original_post = False
            post.matched_by = None
            post.is_broken = False
            post.save()
