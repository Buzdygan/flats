import logging
import json
from abc import ABC, abstractmethod
from typing import Optional, Iterable, List

import numpy as np
from django.db.models.query import QuerySet

from flat_crawler.models import Flat, FlatPost, MatchingFlatPostGroup
from flat_crawler.utils.base_utils import elements_to_str
from flat_crawler.utils.img_utils import bytes_to_images
from flat_crawler.utils.img_matching import ImageMatchingEngine, FlatPostImage

logger = logging.getLogger(__name__)

ORIGINAL_POST = "original_post"


def _fuzzy_equal(a, b, margin):
    return b - margin <= a <= b + margin


class BaseMatcher(object):
    MATCH_TYPE = None

    def __init__(self, post: FlatPost):
        self._post = post

    def find_matches(self, candidates: QuerySet) -> Optional[Iterable[FlatPost]]:
        matches = self._match_candidates(candidates)
        if len(matches) > 0:
            if len(matches) == 1:
                logger.debug(
                    f"{self._post} matched to {matches[0]} by {self.MATCH_TYPE}"
                )
            else:
                matches_str = elements_to_str(matches)
                logger.warning(
                    f"Multiple matches for post: {self._post} using {self.MATCH_TYPE}:\n"
                    f"{matches_str}"
                )
            return matches

    def _match_candidates(self, candidates: QuerySet):
        return [cand for cand in candidates if self._match(cand)]

    @abstractmethod
    def _match(self, candidate: FlatPost) -> bool:
        raise NotImplementedError


# Currently not used
class ThumbnailMatcher(BaseMatcher):
    MATCH_TYPE = "thumbnail"

    def _match_candidates(self, candidates):
        return list(candidates.filter(thumbnail=self._post.thumbnail))


def _extract_fp_images(post: FlatPost) -> List[FlatPostImage]:
    images = bytes_to_images(post.photos_bytes)
    if len(images) > 0:
        return [FlatPostImage(flat_post=post, image=img, img_pos=pos)
                for pos, img in enumerate(images)
        ]
    else:
        logger.warning(f"Missing photos for {post}")
        return []


class ImageMatcher(BaseMatcher):
    MATCH_TYPE = "image"

    EXACT_THRESHOLD = 2
    CONFIDENT_THRESHOLD = 2
    MAYBE_THRESHOLD = 4

    def __init__(self, post, matching_engine: ImageMatchingEngine, dry: bool = False):
        super().__init__(post=post)
        self._engine = matching_engine
        self._fp_images = _extract_fp_images(post=post)
        self._dry = dry

    def _match(self, candidate: FlatPost) -> bool:
        cand_images = _extract_fp_images(post=candidate)
        matches = [self._engine.get_image_match(img1, img2, dry=self._dry)
                   for img1 in self._fp_images for img2 in cand_images
        ]
        exact_matches, confident_matches, maybe_matches = 0, 0, 0
        for match in filter(lambda x: x is not None, matches):
            if match.num_comparers_confirmed == self._engine.num_comparers:
                exact_matches += 1
            elif match.num_comparers_confirmed > 0:
                confident_matches += 1
            elif match.num_comparers_maybe_matched == self._engine.num_comparers:
                maybe_matches += 1

        thresholds = [
            (exact_matches, self.EXACT_THRESHOLD),
            (exact_matches + confident_matches, self.CONFIDENT_THRESHOLD),
            (exact_matches + confident_matches + maybe_matches, self.MAYBE_THRESHOLD)
        ]

        lower_thresholds = False
        if (self._post.price == candidate.price or
            (self._post.size_m2 == candidate.size_m2 and
             _fuzzy_equal(self._post.price, candidate.price, 3000)) or
            self._post.heading == candidate.heading
        ):
            lower_thresholds = True

        for match_num, threshold in thresholds:
            if lower_thresholds:
                threshold -= 1
            if match_num >= threshold:
                return True

        if exact_matches + confident_matches + maybe_matches > 0:
            print(f"Close: {candidate.heading}, {candidate.size_m2}m2, {candidate.price}zł")
            print(f"Exact {exact_matches}, confident: {confident_matches}, maybe: {maybe_matches}")

        return False


class BaseInfoMatcher(BaseMatcher):
    MATCH_TYPE = "base_info"

    def _match(self, candidate: FlatPost) -> bool:
        if self._any(candidate=candidate, fields=["url", "desc"]):
            return True

        if self._all(candidate=candidate, fields=["size_m2", "heading", "district"]):
            return True

    def _any(self, candidate, fields):
        return any(
            getattr(self._post, field) == getattr(candidate, field) for field in fields
        )

    def _all(self, candidate, fields):
        return all(
            getattr(self._post, field) == getattr(candidate, field) for field in fields
        )

image_matching_engine = ImageMatchingEngine(stop_early=True)


class MatchingEngine(object):
    MATCHERS_CONFIG = [
        (BaseInfoMatcher, {}),
        (ImageMatcher, {'matching_engine': image_matching_engine}),
    ]

    def __init__(self, match_broken=False, rematch_mode: bool = False):
        self._match_broken = match_broken
        self._rematch_mode = rematch_mode

    def match_posts(self):
        unmatched_posts = FlatPost.objects.filter(flat__isnull=True)
        # Filter out broken posts, unless we do want to match them.
        if not self._match_broken:
            unmatched_posts = unmatched_posts.filter(is_broken=False)
        unmatched_posts = list(unmatched_posts)
        num_unmatched = len(unmatched_posts)
        logger.info(f"Matching {num_unmatched} unmatched posts.")
        failed_matches = []
        num_created = 0
        num_matched = 0
        num_exceptions = 0
        for post in unmatched_posts:
            logger.info(f"Matching post: {post.heading}, {post.size_m2}m2, {post.price}zł")
            try:
                candidates = self._get_candidates(post=post)
                matches, match_type = self._find_matches(post=post, candidates=candidates)
                if matches is None:
                    self._create_flat_from_post(post=post)
                    num_created += 1
                elif len(matches) == 1:
                    self._match_post_to_existing_flat(
                        post=post, match=matches[0], match_type=match_type
                    )
                    num_matched += 1
                else:
                    self._handle_multiple_matches(post=post, matches=matches)
                    failed_matches.append(post)
            except Exception as exc:
                logger.exception(f"Matching {post} failed with {exc}")
                post.is_broken = True
                post.exception_str = str(exc)
                post.save()
                num_exceptions += 1

        logger.warning(
            f"Following posts failed to match:\n {elements_to_str(failed_matches)}"
        )
        logger.info(
            f"Matching summary:\n"
            f"{num_created} flats created.\n"
            f"{num_matched} posts matched to existing flats.\n"
            f"{len(failed_matches)} posts failed to match\n"
            f"{num_exceptions} posts were broken."
        )

    @classmethod
    def merge_multiple_posts(cls, posts: Iterable[FlatPost]):
        posts_str = elements_to_str(posts)
        posts_without_flat = [post for post in posts if post.flat is None]
        flats = list(set(post.flat for post in posts if post.flat is not None))
        if len(flats) == 0:
            logger.warning(f"Merging posts without flats:\n {posts_str}")
        elif len(flats) == 1:
            logger.warning(f"Merging posts already merged:\n {posts_str}")
            flat = flats[0]
            for post in posts_without_flat:
                post.flat = flat
                post.save()
        else:
            logger.info(f"Merging posts:\n {posts_str}")
            flats.sort(key=lambda flat: flat.created)
            main_flat = flats[0]
            main_flat.hearted = any(flat.hearted for flat in flats)
            main_flat.starred = not main_flat.hearted and any(flat.starred for flat in flats)
            main_flat.rejected = (
                not main_flat.hearted and
                not main_flat.starred and
                any(flat.rejected for flat in flats)
            )
            main_flat.save()
            for flat in flats[1:]:
                logger.info(f"Merging flat {flat} into {main_flat}")
                for related_post in flat.flatpost_set.all():
                    related_post.flat = main_flat
                    related_post.is_original_post = False
                    related_post.save()
                flat.delete()
            for post in posts_without_flat:
                post.flat = main_flat
                post.save()

    def rematch_posts(self, rematched_posts: List[FlatPost]):
        self._rematch_mode = True
        num_rematched = len(rematched_posts)
        logger.info(f"Rematching {num_rematched} posts.")
        failed_matches = []
        num_rematched = 0
        num_exceptions = 0
        for post in rematched_posts:
            logger.info(f"Rematching post: {post}")
            try:
                matches, match_type = self._find_matches(post=post)
                if matches is None:
                    continue
                if len(matches) >= 1:
                    self._handle_multiple_matches(post=post, matches=matches)
                    num_rematched += 1
            except Exception as exc:
                logger.exception(f"Matching {post} failed with {exc}")
                post.is_broken = True
                post.exception_str = str(exc)
                post.save()
                num_exceptions += 1

        logger.info(
            f"Rematching summary:\n"
            f"{num_rematched} posts rematched.\n"
            f"{num_exceptions} posts were broken."
        )

    def _match_post_to_existing_flat(self, post: FlatPost, match: FlatPost, match_type: str):
        flat = match.flat
        logger.info(f"Attaching post: {post} to existing flat: {flat.original_post}")
        flat.min_price = min(flat.min_price, post.price)
        flat.save()
        post.flat = flat
        post.matched_by = match_type
        post.save()

    def _create_flat_from_post(self, post: FlatPost):
        logger.info(f"Creating new Flat from post: {post}")
        new_flat = Flat(min_price=post.price, original_post=post)
        new_flat.save()
        post.flat = new_flat
        post.is_original_post = True
        post.matched_by = ORIGINAL_POST
        post.save()

    def _handle_multiple_matches(self, post: FlatPost, matches: Iterable[FlatPost]):
        posts = [post] + list(matches)
        self.merge_multiple_posts(posts=posts)
        # matches_ids = ",".join(sorted(map(str, (p.id for p in posts))))
        # logger.warning(f"Multiple posts matching: {matches_ids}")
        # group, created = MatchingFlatPostGroup.objects.get_or_create(group_id_hash=matches_ids)
        # if created:
        #     for matched_post in posts:
        #         group.posts.add(matched_post)

    def _get_candidates(self, post: FlatPost):
        flat_q = FlatPost.objects.filter(is_original_post=True)
        flat_q = flat_q.filter(size_m2__gte=post.size_m2 - 1)
        flat_q = flat_q.filter(size_m2__lte=post.size_m2 + 1)
        flat_q = flat_q.filter(price__lte=post.price + 100000)
        flat_q = flat_q.filter(price__gte=post.price - 100000)
        return flat_q

    def _find_matches(self, post: FlatPost, candidates) -> Optional[Iterable[FlatPost]]:
        if not self._rematch_mode:
            assert post.flat is None, "Don't match posts already matched"
            assert (
                not post.is_original_post is None
            ), "Unmatched post has is_original_post=True."

        if candidates.count() > 0:
            assert all(cand.flat is not None for cand in candidates)
            for MatcherCls, config in self.MATCHERS_CONFIG:
                config["post"] = post
                matcher = MatcherCls(**config)
                matches = matcher.find_matches(candidates=candidates)
                if matches:
                    return matches, matcher.MATCH_TYPE
        return None, None
