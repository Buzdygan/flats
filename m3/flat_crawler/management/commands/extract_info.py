
from typing import List, Optional
from collections import Counter

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from flat_crawler.utils.location import extract_locations_from_text, fetch_location_geo, get_geoapi_key
from flat_crawler.utils.extract_info import extract_keys_from_text
from flat_crawler.utils.text_utils import get_colored_text, TextColor, simplify_text
from flat_crawler.models import FlatPost, Location



class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--limit', nargs='?', type=int, default=None)
        parser.add_argument(
            '--locations', action='store_true', help='Search for locations',
        )
        parser.add_argument(
            '--geodata', action='store_true', help='Fetch geodata for locations',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        posts = FlatPost.objects.annotate(num_locations=Count('locations'))
        if options['locations']:
            posts = posts.filter(num_locations=0)
            self._extract_locations(posts=posts, limit=limit)
        elif options['geodata']:
            locations = Location.objects.annotate(
                num_posts=Count('flatpost')
            ).filter(num_posts__gt=0, geolocation_data__isnull=True)
            self._extract_geodata(locations, limit=limit)
        else:
            self._extract_info(posts=posts.all(), limit=limit)

    def _extract_geodata(self, locations, limit=None):
        api_key = get_geoapi_key()
        for num, location in enumerate(locations):
            if limit and num >= limit:
                break
            fetch_location_geo(location=location, api_key=api_key)
        print(f"Fetched geo data for {num} locations")

    def _extract_info(self, posts, limit=None):
        num_posts = len(posts)
        all_keys = Counter()
        for num, fp in enumerate(posts):
            if limit and num >= limit:
                break
            text = fp.heading + '\n' + fp.desc
            text = '\n'.join(filter(lambda x: x, text.split('\n')))
            keys, match_ranges = extract_keys_from_text(text=text)
            if keys:
                self._display_extracted_info(text, keys, match_ranges)
                all_keys.update(keys)
            else:
                print(f"No info for: {fp.heading}")

        print(f"Total posts: {num_posts}")
        for key, num_matched in all_keys.items():
            pct = 100.0 * num_matched / (num + 1)
            print(f"{key}: {pct:.2f}%")


    def _extract_locations(self, posts, limit=None):
        num_matched = 0
        for num, fp in enumerate(posts):
            if limit and num >= limit:
                break
            if fp.locations.count():
                num_matched += 1
                continue

            text = simplify_text(fp.heading + '\n' + fp.desc)
            locs, matches = extract_locations_from_text(text=text, district=fp.district)
            if locs:
                num_matched += 1
                self._display_extracted_info(text, [loc.short_name for loc in locs], matches)
                for loc in locs:
                    fp.locations.add(loc)
                fp.save()
            else:
                print(get_colored_text(text, colored_ranges=[(0, len(text))], color=TextColor.BLUE))
            print(f"{num_matched} / {num + 1}")


    def _display_extracted_info(self, text: str, results: List[str], match_ranges):
        print('\n' * 3)
        print(get_colored_text(text, colored_ranges=match_ranges))
        print('----------------------------------------------')
        print(','.join(results))
        print('\n' * 3)
