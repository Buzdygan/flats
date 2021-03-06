
from typing import List, Optional
from collections import Counter, defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from flat_crawler.utils.location import extract_locations_from_text, fetch_location_geo, get_geoapi_key, get_locations_from_selected_districts, get_location_phrases_dict, get_posts_in_search_area
from flat_crawler.utils.extract_info import extract_keys_from_text
from flat_crawler.utils.text_utils import get_colored_text, TextColor, simplify_text
from flat_crawler.models import FlatPost, Location, SearchArea
from flat_crawler.constants import SELECTED_DISTRICTS

SEARCH_AREAS_FILENAME = '../various/maps/maps_polygons.txt'


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--display-key', nargs='?', type=str, default=None)
        parser.add_argument('--limit', nargs='?', type=int, default=None)
        parser.add_argument(
            '--locations', action='store_true', help='Search for locations',
        )
        parser.add_argument(
            '--geodata', action='store_true', help='Fetch geodata for locations',
        )
        parser.add_argument(
            '--parse-geodata', action='store_true', help='Parse geodata for locations',
        )
        parser.add_argument(
            '--read-search-areas', action='store_true', help='Read search area files',
        )
        parser.add_argument(
            '--attach-areas', action='store_true', help='Attach areas to posts',
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        posts = FlatPost.objects.annotate(num_locations=Count('locations'))
        posts = posts.filter(district__in=SELECTED_DISTRICTS)
        if options.get('locations'):
            posts = posts.filter(num_locations=0, tried_to_extract_locations=False)
            self._extract_locations(posts=posts, limit=limit)
        elif options.get('geodata'):
            locations = Location.objects.annotate(
                num_posts=Count('flatpost')
            ).filter(num_posts__gt=0, geolocation_data__isnull=True)
            self._extract_geodata(locations, limit=limit)
        elif options.get('parse_geodata'):
            locations = Location.objects.filter(geolocation_data__isnull=False)
            self._parse_geodata(locations)
        elif options.get('read_search_areas'):
            self._read_search_areas()
        elif options.get('attach_areas'):
            posts = posts.filter(num_locations__gt=0)
            self._attach_areas_to_posts(posts=posts)
        else:
            self._extract_info(posts=posts.all(), limit=limit, display_key=options.get('display_key'))

    def _read_search_areas(self):

        def _save_area(name, points):
            SearchArea.objects.filter(name=name).delete()
            SearchArea(name=name, points=points).save()

        curr_name = None
        curr_points = []
        with open(SEARCH_AREAS_FILENAME, 'r') as f:
            for line in f:
                sline = line.strip()
                if sline.startswith('<end>'):
                    if len(curr_points) > 2:
                        _save_area(curr_name, curr_points)
                elif sline.startswith('<name>'):
                    curr_name = sline[len('<name>'):]
                    curr_points = []
                else:
                    lng, lat, _ = sline.split(',')
                    curr_points.append((float(lng), float(lat)))

    def _extract_geodata(self, locations, limit=None):
        api_key = get_geoapi_key()
        N = len(locations)
        for num, location in enumerate(locations):
            if limit and num >= limit:
                break
            fetch_location_geo(location=location, api_key=api_key)
            if num % 10 == 0:
                print(f"Fetched {num} / {N}")
        print(f"Fetched geo data for all {N} locations")

    def _parse_geodata(self, locations):
        parsed = 0
        for loc in locations:
            if loc.geolocation_data is None:
                continue
            results = loc.geolocation_data['results']
            try:
                result = results[0] # ignore additional results
                geometry = result['geometry']
                bounds = geometry.get('bounds', geometry['viewport'])
                loc.lat = geometry['location']['lat']
                loc.lng = geometry['location']['lng']
                loc.ne_lat = bounds['northeast']['lat']
                loc.ne_lng = bounds['northeast']['lng']
                loc.sw_lat = bounds['southwest']['lat']
                loc.sw_lng = bounds['southwest']['lng']
                loc.location_types = ','.join(result['types'])
                loc.save()
                parsed += 1
            except:
                print(f"Exception for {loc.full_name}\n{loc.geolocation_data}")
                raise
        print(f"Successfully parsed {parsed} locations geodata.")
        
    def _extract_info(self, posts, limit=None, display_key=None):
        num_posts = len(posts)
        all_keys = Counter()
        for num, fp in enumerate(posts):
            if limit and num >= limit:
                break
            text = fp.heading + '\n' + fp.desc
            text = '\n'.join(filter(lambda x: x, text.split('\n')))
            keys, match_ranges = extract_keys_from_text(text=text)
            if display_key and display_key in keys:
                self._display_extracted_info(text, keys, match_ranges)
            elif not display_key and keys:
                self._display_extracted_info(text, keys, match_ranges)
                all_keys.update(keys)
                fp.keywords = ','.join(keys)
                fp.save()

        print(f"Total posts: {num_posts}")
        for key, num_matched in all_keys.items():
            pct = 100.0 * num_matched / (num + 1)
            print(f"{key}: {pct:.2f}%")

        print(display_key)


    def _extract_locations(self, posts, limit=None):
        locations = get_locations_from_selected_districts()
        locs_phrase_dict = get_location_phrases_dict(locations)
        num_matched = 0
        for num, fp in enumerate(posts):
            if limit and num >= limit:
                break
            if fp.locations.count():
                num_matched += 1
                continue

            text = simplify_text(fp.heading + '\n' + fp.desc).lower()
            locs, matches = extract_locations_from_text(loc_phrase_dict=locs_phrase_dict, text=text, district=fp.district)
            if locs:
                num_matched += 1
                self._display_extracted_info(text, [loc.short_name for loc in locs], matches)
                for loc in locs:
                    fp.locations.add(loc)
            else:
                print(get_colored_text(text, colored_ranges=[(0, len(text))], color=TextColor.BLUE))
            fp.tried_to_extract_locations = True
            fp.save()
            print(f"{num_matched} / {num + 1}")

    def _attach_areas_to_posts(self, posts):
        area_cnt = defaultdict(int)
        for area in SearchArea.objects.all():
            print(f'Attaching {area.name}')
            posts_without_area = posts.exclude(areas__id=area.id)
            for post, score in get_posts_in_search_area(area, posts_without_area):
                # print(post.heading)
                # print('\n'.join(post.locations.all().values_list('full_name', flat=True)))
                # print(f'{area.name}, score: {score}')
                # print('------------------')
                post.areas.add(area)
                area_scores = post.area_scores or []
                post.area_scores = area_scores + [(area.name, score)]
                post.save()
                area_cnt[area.name] += 1
        print(area_cnt.items())


    def _display_extracted_info(self, text: str, results: List[str], match_ranges):
        print('\n' * 3)
        print(get_colored_text(text, colored_ranges=match_ranges))
        print('----------------------------------------------')
        print(','.join(results))
        print('\n' * 3)
