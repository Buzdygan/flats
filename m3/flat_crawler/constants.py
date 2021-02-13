
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


SELECTED_DISTRICTS = [
    MOKOTOW,
    OCHOTA,
    SRODMIESCIE,
    ZOLIBORZ,
]


IGNORED_DISTRICTS = [
    BEMOWO,
    BIALOLEKA,
    BIELANY,
    PRAGA_POLUDNIE,
    PRAGA_POLNOC,
    REMBERTOW,
    TARGOWEK,
    URSUS,
    URSYNOW,
    WAWER,
    WESOLA,
    WILANOW,
    WOLA,
    WLOCHY
]

OTODOM_SEARCH_URL = 'otodom.pl/sprzedaz/mieszkanie/?search%5Bfilter_float_price%3Afrom%5D=400000&search%5Bfilter_float_price%3Ato%5D=1300000&search%5Bfilter_float_m%3Afrom%5D=40&search%5Bfilter_float_m%3Ato%5D=90&search%5Bfilter_enum_market%5D=secondary&search%5Bfilter_float_building_floors_num%3Ato%5D=8&search%5Bfilter_float_build_year%3Ato%5D=1960&locations%5B0%5D%5Bregion_id%5D=7&locations%5B0%5D%5Bsubregion_id%5D=197&locations%5B0%5D%5Bcity_id%5D=26&locations%5B0%5D%5Bdistrict_id%5D=39&locations%5B1%5D%5Bregion_id%5D=7&locations%5B1%5D%5Bsubregion_id%5D=197&locations%5B1%5D%5Bcity_id%5D=26&locations%5B1%5D%5Bdistrict_id%5D=300420&locations%5B2%5D%5Bregion_id%5D=7&locations%5B2%5D%5Bsubregion_id%5D=197&locations%5B2%5D%5Bcity_id%5D=26&locations%5B2%5D%5Bdistrict_id%5D=961&locations%5B3%5D%5Bregion_id%5D=7&locations%5B3%5D%5Bsubregion_id%5D=197&locations%5B3%5D%5Bcity_id%5D=26&locations%5B3%5D%5Bdistrict_id%5D=44'


# Units to seconds
MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR