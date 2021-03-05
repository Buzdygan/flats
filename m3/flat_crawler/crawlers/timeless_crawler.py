import logging
import datetime

from flat_crawler.crawlers.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)

class TimelessCrawler(BaseCrawler):

    def __init__(self, max_pages_without_posts=3, **kwargs):
        super().__init__(**kwargs)
        self._max_pages_without_posts = max_pages_without_posts

    def fetch_new_posts(self):
        logger.info(f"Crawling posts on {self.SOURCE}")
        newest_dt = datetime.datetime(1900, 1, 1)
        oldest_dt = datetime.datetime.now()
        # This assumes going back in time.
        pages_without_posts = 0
        for post_page_url in self._get_post_pages_to_crawl():
            had_new_posts, newest_dt, oldest_dt = self._parse_post_page(
                post_page_url=post_page_url,
                newest_post_dt=newest_dt,
                oldest_post_dt=oldest_dt
            )
            if had_new_posts:
                logger.info("New posts found.")

            if had_new_posts:
                pages_without_posts = 0
            else:
                pages_without_posts += 1
                logger.info(f"No new posts, (pages without posts={pages_without_posts})")

            if pages_without_posts > self._max_pages_without_posts:
                logger.info(f"Stop crawling. {pages_without_posts} pages didn't have new posts")
                break
