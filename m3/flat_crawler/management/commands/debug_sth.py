from itertools import combinations

from django.core.management.base import BaseCommand, CommandError

from flat_crawler.utils.flat_post_matcher import ImageMatcher, _extract_fp_images
from flat_crawler.utils.img_matching import ImageMatchingEngine
from flat_crawler.models import Flat, FlatPost, ImageMatch

from flat_crawler.utils.location import get_locations_for_post
from flat_crawler.models import FlatPost

class Command(BaseCommand):
    def handle(self, *args, **options):
        num_total, num_matched = 0, 0
        for fp in FlatPost.objects.all():
            if get_locations_for_post(fp):
                num_matched += 1
            num_total += 1
            print(f"{num_matched} / {num_total}")
            if num_total > 30:
                break


        # Image matching
        # engine = ImageMatchingEngine()
        # fposts = FlatPost.objects.all()
        # N = len(fposts) * (len(fposts) - 1)
        # for i, (fp1, fp2) in enumerate(combinations(fposts, 2)):
        #     print(f"{i} / {N}")
        #     imgs1 = _extract_fp_images(post=fp1)
        #     imgs2 = _extract_fp_images(post=fp2)
        #     for img1, img2 in [(a, b) for a in imgs1 for b in imgs2]:
        #         try:
        #             res = engine.compare_images(img1.image, img2.image)
        #         except Exception as exc:
        #             print(
        #                 f"Exception for posts ({fp1.id}, {fp2.id})\n"
        #                 f"\tImg1:{img1.img_pos} shape:{img1.image.size}\n"
        #                 f"\tImg2:{img2.img_pos} shape:{img2.image.size}"
        #             )
        #             raise
