import logging
from typing import List, Optional
from functools import reduce

import requests
from django.db.models import Q
from urllib import parse
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

import flat_crawler.constants as ct
from flat_crawler.models import Location, FlatPost, SearchArea
from flat_crawler import exceptions
from flat_crawler.utils.extract_info import extract_keys_from_text, Pattern, LOCATION_PATTERNS
from flat_crawler.utils.text_utils import simplify_text

logger = logging.getLogger(__name__)


DISTRICT_LOCNAME_DICT = {
    ct.SRODMIESCIE: "Śródmieście",
    ct.BEMOWO: 'Bemowo',
    ct.BIALOLEKA: 'Białołęka',
    ct.BIELANY: 'Bielany',
    ct.MOKOTOW: 'Mokotów',
    ct.OCHOTA: 'Ochota',
    ct.PRAGA_POLUDNIE: 'Praga-Południe',
    ct.PRAGA_POLNOC: 'Praga-Północ',
    ct.REMBERTOW: 'Rembertów',
    ct.TARGOWEK: 'Targówek',
    ct.URSUS: 'Ursus',
    ct.URSYNOW: 'Ursynów',
    ct.WAWER: 'Wawer',
    ct.WESOLA: 'Wesoła',
    ct.WILANOW: 'Wilanów',
    ct.WOLA: 'Wola',
    ct.WLOCHY: 'Włochy',
    ct.ZOLIBORZ: 'Żoliborz',
}


def get_district_local_name(district: str) -> str:
    """ Returns real district name, e.g. srodmiescie -> Śródmieście.
        It should match district names in Location.districts_local_names.
        If already a local name, return district.
    """
    if district in DISTRICT_LOCNAME_DICT:
        return DISTRICT_LOCNAME_DICT[district]
    elif district in DISTRICT_LOCNAME_DICT.values():
        return district

    raise exceptions.NotRecognizedDistrict(f"Don't recognize district: {district}")


def get_locations_from_selected_districts():
    query = Q()
    for dist in ct.SELECTED_DISTRICTS:
        dist_loc = get_district_local_name(district=dist)
        query = query | Q(districts_local_names__contains=dist_loc)
    return Location.objects.filter(query)


LOCATION_PREFIXES = ['przy', 'ulic']


def _match_location(text, location, loc_pos_matches):

    def _patt(word):
        return Pattern(key='loc', word=word, max_dist=0, lower=True)

    base_locs = list(map(simplify_text, [location.full_name, location.by_name, location.short_name]))
    _, matches = extract_keys_from_text(text, patterns=list(map(_patt, base_locs)))
    if matches:
        return matches

    prefs, sufs = LOCATION_PREFIXES, []
    for loc_name in base_locs:
        frags = loc_name.split()
        if frags:
            prefs.append(frags[0])
            suf_frags = [f for f in frags[1:] if len(f) > 3]
            if suf_frags:
                sufs.append(' '.join(suf_frags))

    for suf in sufs:
        if extract_keys_from_text(text, patterns=[_patt(suf)])[1]:
            patts = [_patt(pref + ' ' + suf) for pref in prefs]
            _, matches = extract_keys_from_text(text, patterns=patts)
            if matches:
                return matches


def _get_loc_pos_matches(text: str):
    return extract_keys_from_text(text, patterns=LOCATION_PATTERNS)[1]


def _filter_locations_by_text(text: str, locations):
    selected = []
    all_matches = []
    # loc_pos_matches = _get_loc_pos_matches(text)
    for location in locations:
        matches = _match_location(text, location, loc_pos_matches=None)
        if matches:
            selected.append(location)
            all_matches += matches
    return selected, all_matches


def extract_locations_from_text(text: str, district=None):
    text = text
    locations = get_locations_from_selected_districts()
    # if district give, try searching in it first
    if district:
        district_lname = get_district_local_name(district)
        dist_locations = locations.filter(districts_local_names__contains=district_lname)
        selected, matches = _filter_locations_by_text(text=text, locations=dist_locations)
        if selected:
            return selected, matches
        locations = locations.exclude(districts_local_names__contains=district_lname)
    # if district not give or no locations found, try all locations
    return _filter_locations_by_text(text=text, locations=locations)

def _get_location_query(location):
    query_elems = ['Warszawa']
    districts = location.districts_local_names.split(',')
    if len(districts) == 1:
        query_elems.append(districts[0])
    query_elems.append(location.full_name)
    query_str = parse.quote(','.join(query_elems))
    return query_str


def get_geoapi_key():
    with open('gapi.key', 'r') as f:
        return f.read().strip('\n')


def fetch_location_geo(location, api_key):
    if location.geolocation_data is not None:
        return
    query_str = _get_location_query(location)
    if query_str:
        req_url = (
            f'https://maps.googleapis.com/maps/api/geocode/json?address={query_str}&key={api_key}'
        )
        try:
            resp = requests.get(req_url)
            if resp.ok:
                location.geolocation_data = resp.json()
                location.save()
        except Exception as exc:
            logger.exception(f"Couldn't fetch geo data for location: {location.full_name}")
            raise


def location_in_area(location: Location, area: Polygon) -> bool:
    points = [
        Point(location.lng, location.lat),
    ]




def get_posts_in_search_area(search_area: SearchArea):
    area_polygon = Polygon(search_area.points)
