import logging
import hashlib

from abc import ABC
from io import BytesIO
from typing import Iterable, Tuple
from datetime import datetime

import requests
from PIL import Image
from bs4 import BeautifulSoup

from flat_crawler.constants import THUMBNAIL_SIZE, CITY_WARSAW
from flat_crawler.models import FlatPost, PostHash
from flat_crawler.crawlers.helpers import get_img_and_bytes_from_url


class CrawlingException(Exception):
    pass


class URLFailedToLoadException(CrawlingException):
    pass


class PostHeadingMissing(CrawlingException):
    pass


class PostURLMissing(CrawlingException):
    pass


class PostFailedToSave(CrawlingException):
    pass


class BasePostFilter(ABC):
    def ignore_post(self, post: FlatPost) -> bool:
        raise NotImplementedError

    def ignore_detailed_post(self, post: FlatPost) -> bool:
        raise NotImplementedError


class NoopFilter(BasePostFilter):
    def ignore_post(self, post: FlatPost) -> bool:
        return False

    def ignore_detailed_post(self, post: FlatPost) -> bool:
        return False


class BaseCrawler(ABC):
    SOURCE = None

    def __init__(
        self,
        start_dt: datetime,
        post_filter=None,
        allow_pages_without_new_posts=False,
        pages_limit=100,
        city=CITY_WARSAW,
    ):
        self._start_dt = start_dt
        self._post_filter = post_filter if post_filter is not None else NoopFilter()
        self._allow_pages_without_new_posts = allow_pages_without_new_posts
        self._pages_limit = pages_limit
        self._city = city
        self._post_hashes = set(
            PostHash.objects.filter(source=self.SOURCE).values_list('post_hash', flat=True) # pylint: disable=no-member
        )

    def fetch_new_posts(self):
        for post_page_url in self._get_post_pages_to_crawl(
            page_start=1, page_stop=self._pages_limit
        ):
            had_new_posts, oldest_dt = self._parse_post_page(
                post_page_url=post_page_url
            )
            if not self._allow_pages_without_new_posts and not had_new_posts:
                logging.info(f"Stop crawling, {post_page_url} didn't have new posts")
                break

            if oldest_dt < self._start_dt:
                logging.info(f"Stop crawling, fetched all posts since {oldest_dt}")
                break

    def _parse_post_page(self, post_page_url: str):
        logging.info(f"Parsing posts on page: {post_page_url}")
        soup = self._get_soup_from_url(url=post_page_url)
        new_posts = False
        oldest_post = datetime.now()
        for post_soup in self._extract_posts_from_page_soup(page_soup=soup):
            post_hash, is_present = self._get_post_hash(post_soup=post_soup)
            if is_present:
                logging.info("Skipping post, already present.")
                continue
            new_posts = True
            post_sketch = self._post_from_soup(soup=post_soup)
            post_sketch.post_hash = post_hash
            post_sketch.post_soup = post_soup.encode()
            if not post_sketch.dt_posted:
                logging.warning(
                    f"Date added not found for post: {post_sketch}. Setting to {oldest_post}"
                )
                post_sketch.dt_posted = oldest_post
            self._validate_post(source_url=post_page_url, post=post_sketch)
            self._process_post_sketch(post_sketch=post_sketch)
            self._save_post(post=post_sketch)
            oldest_post = min(oldest_post, post_sketch.dt_posted)
        return new_posts, oldest_post

    def _process_post_sketch(self, post_sketch: FlatPost) -> None:
        post_sketch.city = self._city
        if self._ignore_post(post=post_sketch):
            return

        details_soup = self._get_soup_from_url(url=post_sketch.url)
        try:
            self._add_details(post=post_sketch, details_soup=details_soup)
            if self._ignore_detailed_post(post=post_sketch):
                return
            post_sketch.details_added = True
        except CrawlingException:
            logging.exception(f"Exception when adding details to post: {post_sketch}")

        self._process_post_before_save(post=post_sketch)

    def _save_post(self, post: FlatPost) -> None:
        logging.info(f"Saving FlatPost: {post}")
        try:
            post.save()
        except Exception as exc:
            logging.error(f"{post} Failed to be saved")
            raise PostFailedToSave(exc)

    def _add_thumbnail(self, post: FlatPost, img_url: str):
        _, img_bytes = get_img_and_bytes_from_url(
            img_url=img_url, resize=THUMBNAIL_SIZE
        )
        post.thumbnail = img_bytes.getvalue()

    def _get_post_hash(self, post_soup: BeautifulSoup) -> Tuple[str, bool]:
        post_hash = hashlib.md5(post_soup.encode()).hexdigest()
        existing = post_hash in self._post_hashes
        if not existing:
            PostHash(source=self.SOURCE, post_hash=post_hash).save()
            self._post_hashes.add(post_hash)
        return post_hash, existing

    def _process_post_before_save(self, post: FlatPost) -> None:
        pass

    def _validate_post(self, source_url: str, post: FlatPost) -> None:
        if not post.heading:
            raise PostHeadingMissing(f"Post from {source_url} misses header.")

        if not post.url:
            raise PostURLMissing(f"Post from {source_url}: {post.heading} misses url.")

    def _ignore_post(self, post: FlatPost) -> bool:
        return self._post_filter.ignore_post(post=post)

    def _ignore_detailed_post(self, post: FlatPost) -> bool:
        return self._post_filter.ignore_detailed_post(post=post)

    def _get_soup_from_url(self, url: str):
        try:
            page = requests.get(url)
            return BeautifulSoup(page.content, "html.parser")
        except Exception as exc:
            logging.error(f"Failed to load url: {url}")
            raise URLFailedToLoadException(exc)

    def _get_post_pages_to_crawl(self, page_start, page_stop):
        raise NotImplementedError

    def _post_from_soup(self, soup: BeautifulSoup) -> FlatPost:
        raise NotImplementedError

    def _add_details(self, post: FlatPost, details_soup: BeautifulSoup) -> None:
        raise NotImplementedError

    def _extract_posts_from_page_soup(
        self, page_soup: BeautifulSoup
    ) -> Iterable[BeautifulSoup]:
        raise NotImplementedError
