import logging
import hashlib

from abc import ABC
from io import BytesIO
from typing import Iterable, Tuple, NamedTuple, Optional, List
import datetime
from datetime import timedelta

from PIL import Image
from bs4 import BeautifulSoup

from flat_crawler.constants import THUMBNAIL_SIZE, CITY_WARSAW
from flat_crawler.models import FlatPost, PostHash, CrawlingLog
from flat_crawler.crawlers.helpers import get_soup_from_url
from flat_crawler.utils.img_utils import get_img_bytes_from_url, img_urls_to_bytes
from flat_crawler.utils.text_utils import deduce_size_from_text
from flat_crawler import exceptions

logger = logging.getLogger(__name__)


class SoupInfo(NamedTuple):
    base: BeautifulSoup
    detailed: BeautifulSoup


class BasePostFilter(ABC):
    def ignore_post(self, post: FlatPost) -> bool:
        raise NotImplementedError


class NoopFilter(BasePostFilter):
    def ignore_post(self, post: FlatPost) -> bool:
        return False

class DistrictFilter(BasePostFilter):
    def __init__(self, ignored_districts=[], **kwargs):
        super().__init__(**kwargs)
        self._ignored_districts = set(ignored_districts)

    def ignore_post(self, post: FlatPost) -> bool:
        if post.district and post.district in self._ignored_districts:
            logger.info(f"Ignoring district {post.district}")
            return True
        return False

DEFAULT_PAGE_STOP = 100
DEFAULT_LOOKBACK_DAYS = 7


class BaseCrawler(ABC):
    SOURCE = None

    def __init__(
        self,
        lookback_days=DEFAULT_LOOKBACK_DAYS,
        post_filter=None,
        allow_pages_without_new_posts=True,
        page_start=1,
        page_stop=DEFAULT_PAGE_STOP,
        city=CITY_WARSAW,
        **kwargs,
    ):
        self._fetch_posts_since_date = datetime.date.today() - timedelta(days=lookback_days)
        self._post_filter = post_filter if post_filter is not None else NoopFilter()
        self._allow_pages_without_new_posts = allow_pages_without_new_posts
        self._page_start = page_start
        self._page_stop = page_stop
        self._city = city
        self._post_hashes = set(
            PostHash.objects.filter(source=self.SOURCE).values_list('post_hash', flat=True) # pylint: disable=no-member
        )

        self._field_getters_dict = {
            'size_m2': self._get_size_m2,
            'city': self._get_city,
            'district': self._get_district,
            'url': self._get_url,
            'thumbnail_url': self._get_thumbnail_url,
            'thumbnail': self._get_thumbnail,
            'price': self._get_price,
            'heading': self._get_heading,
            'desc': self._get_desc,
            'info_dict_json': self._get_info_dict_json,
            'dt_posted': self._get_dt_posted,
        }

        # Those fields will be extracted after initial verification
        # (only if post hasn't been skipped)
        self._postprocessing_field_getters_dict = {
            'photos_bytes': self._get_photos_bytes,
        }

    def fetch_new_posts(self):
        crawl_from_date = self._get_date_to_crawl_from()
        logger.info(
            f"Crawling all posts on {self.SOURCE} since {crawl_from_date}, crawl_id: {self._get_crawl_id()}"
        )
        newest_dt = datetime.datetime(1900, 1, 1)
        oldest_dt = datetime.datetime.now()
        # This assumes going back in time.
        for post_page_url in self._get_post_pages_to_crawl():
            print('DATE RANGE', oldest_dt, newest_dt)
            had_new_posts, newest_dt, oldest_dt = self._parse_post_page(
                post_page_url=post_page_url,
                newest_post_dt=newest_dt,
                oldest_post_dt=oldest_dt
            )

            print('DATE RANGE 2', oldest_dt, newest_dt)
            self._save_crawling_log(oldest_crawled_dt=oldest_dt, newest_crawled_dt=newest_dt)

            if not self._allow_pages_without_new_posts and not had_new_posts:
                logger.info(f"Stop crawling, {post_page_url} didn't have new posts")
                break

            if oldest_dt.date() < crawl_from_date:
                logger.info(f"Stop crawling, fetched all posts since {oldest_dt}")
                break

    def _get_crawl_id(self) -> str:
        return ""

    def _save_crawling_log(self, oldest_crawled_dt, newest_crawled_dt):
        crawl_id = self._get_crawl_id()
        date_crawled = oldest_crawled_dt.date() + timedelta(days=1)
        while date_crawled < newest_crawled_dt.date():
            _, new_date = CrawlingLog.objects.get_or_create(
                source=self.SOURCE, crawl_id=crawl_id, date_fully_crawled=date_crawled
            )
            if new_date:
                logger.info(f"Crawled all posts from {date_crawled} on {self.SOURCE}")
            date_crawled += timedelta(days=1)

    def _get_date_to_crawl_from(self):
        crawl_id = self._get_crawl_id()
        dates_crawled = set(CrawlingLog.objects.filter(
            source=self.SOURCE, crawl_id=crawl_id, date_fully_crawled__gte=self._fetch_posts_since_date
        ).values_list('date_fully_crawled', flat=True))
        date = self._fetch_posts_since_date
        while date < datetime.date.today() and date in dates_crawled:
            date += timedelta(days=1)
        return date

    def _get_post_pages_to_crawl(self):
        for page_num in range(self._page_start, self._page_stop + 1):
            yield self._get_main_url(page_num=page_num)

    def _parse_post_page(self, post_page_url: str, newest_post_dt, oldest_post_dt):
        logger.info(f"Parsing posts on page: {post_page_url}")
        soup = get_soup_from_url(url=post_page_url)
        new_posts = False
        dt_posted_found = False
        for post_soup in self._extract_posts_from_page_soup(page_soup=soup):
            soup_info = SoupInfo(base=post_soup, detailed=None)
            try:
                post_sketch = self._parse_soup_info(soup_info=soup_info)
            except Exception as exc:
                logger.exception(exc)
                continue
            if self._ignore_post(post=post_sketch):
                continue
            self._validate_post(source_url=post_page_url, post=post_sketch)
            if post_sketch.dt_posted:
                dt_posted_found = True
                oldest_post_dt = min(oldest_post_dt, post_sketch.dt_posted)
                newest_post_dt = max(newest_post_dt, post_sketch.dt_posted)
            post_hash, is_present = self._get_post_hash(post=post_sketch)
            if is_present:
                logger.info(f"Skipping post, already present. (new_posts={new_posts})")
                continue
            new_posts = True
            post_sketch.post_hash = post_hash
            post_sketch.post_soup = post_soup.encode()
            try:
                self._process_post_sketch(post_sketch=post_sketch, base_soup=post_soup)
                self._save_post(post=post_sketch)
            except Exception as exc:
                logger.exception(exc)
                continue
        if not dt_posted_found:
            raise exceptions.PostDTPostedMissing(
                f"No post had dt_posted extracted on {post_page_url}"
            )
        return new_posts, newest_post_dt, oldest_post_dt

    def _parse_soup_info(
        self,
        soup_info: SoupInfo,
        post: Optional[FlatPost] = None,
        postprocessing: bool = False,
    ) -> FlatPost:
        post = FlatPost(source=self.SOURCE) if post is None else post

        field_getters_dict = self._field_getters_dict
        if postprocessing:
            field_getters_dict.update(self._postprocessing_field_getters_dict)

        for field, field_getter in field_getters_dict.items():
            if getattr(post, field) is not None:
                # skip as we already have value
                continue
            field_val = field_getter(soup=soup_info)
            if field_val is not None:
                setattr(post, field, field_val)
        return post

    def _process_post_sketch(self, post_sketch: FlatPost, base_soup: BeautifulSoup) -> None:
        detailed_soup = get_soup_from_url(url=post_sketch.url)
        post_sketch.post_detailed_soup = detailed_soup.encode()
        soup_info = SoupInfo(base=base_soup, detailed=detailed_soup)
        try:
            post_sketch = self._parse_soup_info(
                soup_info=soup_info,
                post=post_sketch,
                postprocessing=True
            )
            post_sketch.details_added = True
        except exceptions.CrawlingException:
            logger.exception(f"Exception when adding details to post: {post_sketch}")

    def _ignore_post(self, post: FlatPost) -> bool:
        return self._post_filter.ignore_post(post=post)

    def _validate_post(self, source_url: str, post: FlatPost) -> None:
        if not post.heading:
            raise exceptions.PostHeadingMissing(f"Post from {source_url} misses header.")

        if not post.url:
            raise exceptions.PostURLMissing(f"Post from {source_url}: {post.heading} misses url.")

    def _get_post_hash(self, post: FlatPost) -> Tuple[str, bool]:
        post_bytes = post.heading.encode()
        if post.price is not None:
            post_bytes += str(post.price).encode()
        if post.thumbnail is not None:
            post_bytes += post.thumbnail
        post_hash = hashlib.md5(post_bytes).hexdigest()
        existing = post_hash in self._post_hashes
        if not existing:
            PostHash(source=self.SOURCE, post_hash=post_hash).save()
            self._post_hashes.add(post_hash)
        return post_hash, existing

    def _save_post(self, post: FlatPost) -> None:
        logger.info(f"Saving FlatPost: {post}")
        try:
            post.save()
        except Exception as exc:
            logger.error(f"{post} Failed to be saved")
            raise exceptions.PostFailedToSave(exc)

    def _extract_posts_from_page_soup(
        self, page_soup: BeautifulSoup
    ) -> Iterable[BeautifulSoup]:
        raise NotImplementedError

    def _deduce_size_m2_from_text(self, soup: SoupInfo) -> Optional[str]:
        heading = self._get_heading(soup=soup) or ''
        desc = self._get_desc(soup=soup) or ''
        text = heading + ' ' + desc
        # if we have any text to deduce from
        if text.strip():
            price = self._get_price(soup=soup)
            return deduce_size_from_text(text=text, price=price)

    def _get_size_m2(self, soup: SoupInfo) -> Optional[int]:
        return None

    def _get_city(self, soup: SoupInfo) -> Optional[str]:
        return self._city

    def _get_district(self, soup: SoupInfo) -> Optional[str]:
        return None

    def _get_sub_district(self, soup: SoupInfo) -> Optional[str]:
        return None

    def _get_street(self, soup: SoupInfo) -> Optional[str]:
        return None

    def _get_url(self, soup: SoupInfo) -> Optional[str]:
        return None

    def _get_thumbnail_url(self, soup: SoupInfo) -> Optional[str]:
        return None

    def _get_thumbnail(self, soup: SoupInfo):
        thumbnail_url = self._get_thumbnail_url(soup=soup)
        if thumbnail_url:
            return get_img_bytes_from_url(
                img_url=thumbnail_url, resize=THUMBNAIL_SIZE
            )

    def _get_price(self, soup: SoupInfo) -> Optional[int]:
        return None

    def _get_heading(self, soup: SoupInfo) -> Optional[str]:
        return None

    def _get_desc(self, soup: SoupInfo) -> Optional[str]:
        return None

    def _get_photos_bytes(self, soup: SoupInfo) -> Optional[bytes]:
        img_urls = self._get_img_urls(soup=soup)
        if img_urls is not None:
            return img_urls_to_bytes(img_urls=img_urls)

    def _get_img_urls(self, soup: SoupInfo) -> Optional[List[str]]:
        return None

    def _get_info_dict_json(self, soup: SoupInfo) -> Optional[str]:
        return None

    def _get_dt_posted(self, soup: SoupInfo) -> Optional[datetime.datetime]:
        return None
