import re

from fuzzysearch import find_near_matches
from fuzzywuzzy import fuzz

from flat_crawler import exceptions
from flat_crawler.constants import MINUTE, HOUR, DAY

MIN_SIZE = 10
MAX_SIZE = 1000
MIN_PRICE_PER_M = 3000
MAX_PRICE_PER_M = 30000
AVG_PRICE_PER_M = 11000


class TextColor:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


PL_CHARS_MAP = {
    'ą': 'a',
    'ć': 'c',
    'ę': 'e',
    'ł': 'l',
    'ó': 'o',
    'ś': 's',
    'ź': 'z',
    'ż': 'z',
}


def deduce_size_from_text(text: str, price: int):
    regexp = r"[+-]? *((?:\d+(?:\.\d*)?|\.\d+|)(?:[eE][+-]?\d+)?|(?:\d+(?:\,\d*)?|\,\d+|)(?:[eE][+-]?\d+)?)\s*(m2|metrów|metrow|metry|m kw|m.kw.|m kw.|m. kw|mkw)"

    unit_pattern = re.compile(regexp, re.IGNORECASE)
    found = re.findall(unit_pattern, text)
    if not found:
        return

    floats = []
    for float_str, _ in found:
        float_str = float_str.replace(',', '.')
        try:
            floats.append(float(float_str))
        except Exception:
            pass
    sizes = [size for size in floats if MIN_SIZE <= size <= MAX_SIZE]
    sizes = [size for size in floats
             if MIN_PRICE_PER_M <= price / size <= MAX_PRICE_PER_M]

    if sizes:
        return min(sizes, key=lambda size: abs(price / size - AVG_PRICE_PER_M))


def simplify_text(text: str):
    """ Adjusts text to make it easier to compare against search patterns. """

    text = ' '.join(re.split(r'[.;!?,%:"]', text))
    words = [w for w in text.split() if len(w) > 1]
    return ' '.join(words)

def normalize_word(word: str):
    """ Removes special characters, whitespaces and converts polish characters to english. """
    word = re.sub(r'[.;!?,%:"]', '', word).lower().strip()
    for pl_c, eng_c in PL_CHARS_MAP.items():
        word = re.sub(pl_c, eng_c, word)
    return word


def get_colored_text(text, colored_ranges, color=TextColor.RED):
    colored_ranges.sort()
    curr_end = -1
    opened_color = False
    if len(colored_ranges) > 0:
        colored_text = text[:colored_ranges[0][0]]
    else:
        return text
    for start, end in colored_ranges:
        if start > curr_end:
            if opened_color:
                colored_text += TextColor.END
            colored_text += text[curr_end:start] + color + text[start:end]
        else:
            colored_text += text[curr_end:end]
        curr_end = max(curr_end, end)
        opened_color = True
    if opened_color:
        colored_text += TextColor.END
    colored_text += text[curr_end:]
    return colored_text


UNIT_TO_SECONDS = {
    'sekundę': 1,
    'sekundy': 1,
    'sekund': 1,
    'minutę': MINUTE,
    'minuty': MINUTE,
    'godzinę': HOUR,
    'godziny': HOUR,
    'dni': DAY,
    'dzień': DAY,
}

def parse_timedelta_str_to_seconds(timedelta_str: str) -> int:
    td_str = timedelta_str.lower().replace('temu', ' ')
    els = td_str.split()

    if len(els) == 1:
        num = 1
        unit = els[0]
    elif len(els) == 2:
        num = int(els[0])
        unit = els[1]
    else:
        raise exceptions.InvalidTimedeltaStr(f"Wrong timedelta str: {timedelta_str}")

    return num * UNIT_TO_SECONDS[max(UNIT_TO_SECONDS.keys(), key=lambda x: fuzz.ratio(x, unit))]
