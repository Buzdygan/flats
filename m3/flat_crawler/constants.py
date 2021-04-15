

from django.conf import settings

THUMBNAIL_SIZE = (150, 100)
MINATURE_SIZE = (4, 2)

CITY_WARSAW = 'Warsaw'

# Warsaw districts
BEMOWO = 'bemowo'
BIALOLEKA = 'bialoleka'
BIELANY = 'bielany'
MOKOTOW = 'mokotow'
OCHOTA = 'ochota'
PRAGA_POLUDNIE = 'praga-poludnie'
PRAGA_POLNOC = 'praga-polnoc'
REMBERTOW = 'rembertow'
TARGOWEK = 'targowek'
URSUS = 'ursus'
URSYNOW = 'ursynow'
WAWER = 'wawer'
WESOLA = 'wesola'
WILANOW = 'wilanow'
WOLA = 'wola'
WLOCHY = 'wlochy'
SRODMIESCIE = 'srodmiescie'
ZOLIBORZ = 'zoliborz'


OTODOM_SEARCH_URL = 'otodom.pl/sprzedaz/mieszkanie/?search%5Bfilter_float_price%3Afrom%5D=400000&search%5Bfilter_float_price%3Ato%5D=1300000&search%5Bfilter_float_m%3Afrom%5D=40&search%5Bfilter_float_m%3Ato%5D=90&search%5Bfilter_enum_market%5D=secondary&search%5Bfilter_float_building_floors_num%3Ato%5D=8&search%5Bfilter_float_build_year%3Ato%5D=1960&locations%5B0%5D%5Bregion_id%5D=7&locations%5B0%5D%5Bsubregion_id%5D=197&locations%5B0%5D%5Bcity_id%5D=26&locations%5B0%5D%5Bdistrict_id%5D=39&locations%5B1%5D%5Bregion_id%5D=7&locations%5B1%5D%5Bsubregion_id%5D=197&locations%5B1%5D%5Bcity_id%5D=26&locations%5B1%5D%5Bdistrict_id%5D=300420&locations%5B2%5D%5Bregion_id%5D=7&locations%5B2%5D%5Bsubregion_id%5D=197&locations%5B2%5D%5Bcity_id%5D=26&locations%5B2%5D%5Bdistrict_id%5D=961&locations%5B3%5D%5Bregion_id%5D=7&locations%5B3%5D%5Bsubregion_id%5D=197&locations%5B3%5D%5Bcity_id%5D=26&locations%5B3%5D%5Bdistrict_id%5D=44'

SELECTED_DISTRICTS = settings.SELECTED_DISTRICTS
IGNORED_DISTRICTS = settings.IGNORED_DISTRICTS
MIN_PRICE = settings.DEFAULT_MIN_PRICE
MAX_PRICE = settings.DEFAULT_MAX_PRICE


# Units to seconds
MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR


IMG_BYTES_DELIM = b'$!%'

LOCATION_TYPE_ROUTE = 'route'
LOCATION_TYPE_PARK = 'park'
LOCATION_TYPE_SUBWAY = 'subway_station'
LOCATION_TYPE_TRANSIT = 'transit_station'

AREA_STARY_MOKOTOW = 'stary-mokotow'
BASE_AREA = 'base-area'


KAMIENICA_KEY = 'kamienica'
MODERN_KEY = 'nowoczesne'
DEVELOPER_KEY = 'deweloper'
BALCONY_KEY = 'balkon'
FRENCH_BALCONY_KEY = 'balkon-francuski'

LOCATION_KEY = 'location'