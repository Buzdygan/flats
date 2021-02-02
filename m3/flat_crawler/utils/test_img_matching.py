
import pytest
from itertools import combinations

from PIL import Image

from flat_crawler.utils.img_matching import ImageMatchingEngine
from flat_crawler.utils.img_utils import bytes_to_images


def _load_img(img_id):
    return Image.open(f'static/test_data/images/{img_id}.jpg')


IMAGES = [
    # two images differing only by logo
    _load_img('img_0_a'),
    _load_img('img_0_b'),
    # two images, second is cropped version of first
    _load_img('img_1_a'),
    _load_img('img_1_b'),
    # two images of the same buildings, different angles
    _load_img('img_2_a'),
    _load_img('img_2_b'),
]


def test_img_matcher():
    engine = ImageMatchingEngine()

    # Image should match with itself
    maybe, confirmed, details = engine.compare_images(IMAGES[0], IMAGES[0])
    assert maybe == 0
    assert confirmed == 3

    # Those two are identical photos with different logo
    maybe, confirmed, details = engine.compare_images(IMAGES[0], IMAGES[1])
    assert maybe == 0
    assert confirmed == 3

    # Those two are similar photos, should be catched by hist comparer
    maybe, confirmed, details = engine.compare_images(IMAGES[2], IMAGES[3])
    assert maybe == 0
    assert confirmed == 1
    assert details['HistComparer'] > 0.9

    # Those two are similar photos
    maybe, confirmed, details = engine.compare_images(IMAGES[4], IMAGES[5])
    assert maybe == 0
    assert confirmed == 1
    assert details['HistComparer'] > 0.9

    # Photos of different places should not match
    for img1, img2 in combinations([IMAGES[0], IMAGES[2], IMAGES[4]], 2):
        maybe, confirmed, details = engine.compare_images(img1, img2)
        print(details)
        assert maybe + confirmed == 0
