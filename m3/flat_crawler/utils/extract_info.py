

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