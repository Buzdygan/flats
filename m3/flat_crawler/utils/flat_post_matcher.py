import logging
import json
from abc import ABC, abstractmethod
from typing import Optional, Iterable, List

import numpy as np
from django.db.models.query import QuerySet

from flat_crawler.models import Flat, FlatPost
from flat_crawler.utils.base_utils import elements_to_str

logger = logging.getLogger(__name__)

ORIGINAL_POST = "original_post"

class BaseMatcher(object):
    MATCH_TYPE = None

    def __init__(self, post: FlatPost):
        self._post = post

    def find_matches(self, candidates: QuerySet) -> Optional[Iterable[FlatPost]]:
        matches = self._match_candidates(candidates)
        if len(matches) > 0:
            if len(matches) == 1:
                logger.info(
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


class ThumbnailMatcher(BaseMatcher):
    MATCH_TYPE = "thumbnail"

    def _match_candidates(self, candidates):
        return list(candidates.filter(thumbnail=self._post.thumbnail))


def _extract_signature(post: FlatPost):
    if post.photos_signature_json:
        return np.array(json.loads(post.photos_signature_json))
    else:
        logger.warning(f"Missing photo signature for {post}")


DEFAULT_IMG_MATCH_THRESHOLD = 4


class ImageMatcher(BaseMatcher):
    MATCH_TYPE = "image"

    def __init__(self, post, threshold=DEFAULT_IMG_MATCH_THRESHOLD):
        super().__init__(post=post)
        self._img_arr = _extract_signature(post)
        self._threshold = threshold

    def _match(self, candidate: FlatPost) -> bool:
        cand_img_arr = _extract_signature(candidate)
        if cand_img_arr is None or self._img_arr is None:
            return False

        min_len = min(len(cand_img_arr), len(self._img_arr))
        if min_len <= 1:
            return False

        dists = [np.average(np.abs(a - b)) for a in self._img_arr for b in cand_img_arr]
        score = np.average(sorted(dists)[:min_len])
        return score < self._threshold


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


class MatchingEngine(object):
    MATCHERS_CONFIG = [
        (ThumbnailMatcher, {}),
        (ImageMatcher, {}),
        (BaseInfoMatcher, {}),
    ]

    def __init__(self, match_broken=False):
        self._match_broken = match_broken

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
            logger.info(f"Matching post: {post}")
            try:
                matches, match_type = self._find_matches(post=post)
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
        flats = list(set(post.flat for post in posts if post.flat is not None))
        if len(flats) == 0:
            logger.warning(f"Merging posts without flats:\n {posts_str}")
        elif len(flats) == 1:
            logger.warning(f"Merging posts already merged:\n {posts_str}")
        else:
            logger.info(f"Merging posts:\n {posts_str}")
            main_flat = flats[0]
            for flat in flats[1:]:
                logger.info(f"Merging flat {flat} into {main_flat}")
                for related_post in flat.flatpost_set.all():
                    related_post.flat = main_flat
                    related_post.is_original_post = False
                    related_post.save()
                flat.delete()

    def _match_post_to_existing_flat(self, post: FlatPost, match: FlatPost, match_type: str):
        flat = match.flat
        logger.info(f"Attaching post: {post} to existing flat: {flat}")
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
        matches_ids = ",".join(map(str, (match.id for match in matches)))
        logger.warning(f"Multiple matches found for post: {post}\nIds: {matches_ids}")

    def _get_candidates(self, post: FlatPost):
        flat_q = FlatPost.objects.filter(is_original_post=True)
        flat_q = flat_q.filter(size_m2__gte=float(post.size_m2) - 1)
        flat_q = flat_q.filter(size_m2__lte=float(post.size_m2) + 1)
        return flat_q

    def _find_matches(self, post: FlatPost) -> Optional[Iterable[FlatPost]]:
        assert post.flat is None, "Don't match posts already matched"
        assert (
            not post.is_original_post is None
        ), "Unmatched post has is_original_post=True."

        candidates = self._get_candidates(post=post)
        if candidates.count() > 0:
            assert all(cand.flat is not None for cand in candidates)
            for MatcherCls, config in self.MATCHERS_CONFIG:
                config["post"] = post
                matcher = MatcherCls(**config)
                matches = matcher.find_matches(candidates=candidates)
                if matches:
                    return matches, matcher.MATCH_TYPE
        return None, None
