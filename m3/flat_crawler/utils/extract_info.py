
from typing import NamedTuple, List
from fuzzysearch import find_near_matches


DEVELOPER_KEY = 'developer'
BALCONY_KEY = 'balcony'
FRENCH_BALCONY_KEY = 'french_balcony'

LOCATION_KEY = 'location'


class Pattern(NamedTuple):
    key: str # type of info we want to extract
    word: str
    max_dist: int = 0
    lower: bool = False


PATTERNS = [
    Pattern(key=DEVELOPER_KEY, word='deweloper', max_dist=1, lower=True),
    Pattern(key=DEVELOPER_KEY, word='developer', max_dist=1, lower=True),
    Pattern(key=BALCONY_KEY, word='balkon', max_dist=0, lower=True),
    Pattern(key=BALCONY_KEY, word='balkonem', max_dist=0, lower=True),
    Pattern(key=BALCONY_KEY, word='loggia', max_dist=1, lower=True),
    Pattern(key=FRENCH_BALCONY_KEY, word='balkon francuski', max_dist=3, lower=True),
]

LOCATION_PATTERNS = [
    Pattern(key=LOCATION_KEY, word=word, max_dist=0, lower=True) for word in [
        'obok', 'przy', 'niedaleko', 'zlokalizowane', 'położone', 'w okolicy', 'na', 'ul.',
        'ulicy', 'placu',
    ]
]


def extract_keys_from_text(text: str, patterns=PATTERNS):
    non_lower_pat = [p for p in patterns if not p.lower]
    lower_pat = [p for p in patterns if p.lower]
    keys = set()
    all_matches = []
    lower_text = text.lower()
    for patt in non_lower_pat + lower_pat:
        if patt.lower:
            txt = lower_text
            word = patt.word.lower()
        else:
            txt = text
            word = patt.word
        if not word:
            continue
        matches = find_near_matches(word, txt, max_l_dist=patt.max_dist)
        if matches:
            keys.add(patt.key)
        all_matches.extend(matches)
    return list(keys), [(m.start, m.end) for m in all_matches]
