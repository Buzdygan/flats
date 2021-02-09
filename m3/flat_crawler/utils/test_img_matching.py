
import pytest
from itertools import combinations

from PIL import Image

from flat_crawler.utils.img_matching import ImageMatchingEngine, FlatPostImage
from flat_crawler.utils.img_utils import bytes_to_images
from flat_crawler.models import FlatPost, ImageMatch


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

@pytest.mark.django_db
def test_get_image_match():
    engine = ImageMatchingEngine()

    fp_1 = FlatPost(heading='fp_1')
    fp_1.save()

    fp_2 = FlatPost(heading='fp_2')
    fp_2.save()

    if fp_1.id > fp_2.id:
        fp_1, fp_2 = fp_2, fp_1

    fp_img_1 = FlatPostImage(flat_post=fp_1, image=IMAGES[0], img_pos=0)
    fp_img_2 = FlatPostImage(flat_post=fp_2, image=IMAGES[0], img_pos=1)

    match = engine.get_image_match(fp_img_1, fp_img_2, dry=True)
    assert match is not None
    assert ImageMatch.objects.count() == 0

    match = engine.get_image_match(fp_img_1, fp_img_2)

    assert ImageMatch.objects.count() == 1
    img_match = ImageMatch.objects.get(post_1=fp_1, post_2=fp_2)

    assert match == img_match

    assert img_match.img_pos_1 == 0
    assert img_match.img_pos_2 == 1

    assert img_match.num_comparers_confirmed == 3
    assert img_match.num_comparers_maybe_matched == 0


def test_compare_images():
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
    assert maybe == 1
    assert confirmed == 0
    assert details['SimpleHistComparer'] > 0.9

    # Those two are similar but different photos
    maybe, confirmed, details = engine.compare_images(IMAGES[4], IMAGES[5])
    assert maybe == 0
    assert confirmed == 0
    assert details['SimpleHistComparer'] > 0.7

    # Photos of different places should not match
    for img1, img2 in combinations([IMAGES[0], IMAGES[2], IMAGES[4]], 2):
        maybe, confirmed, details = engine.compare_images(img1, img2)
        print(details)
        assert maybe + confirmed == 0
