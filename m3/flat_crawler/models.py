import logging
import uuid
import base64
import textwrap

import jsonfield
from django.db import models
from urllib import parse

from flat_crawler.utils.img_utils import bytes_to_images
from flat_crawler.constants import IMG_BYTES_DELIM, AREA_STARY_MOKOTOW

logger = logging.getLogger(__name__)


class Source(models.TextChoices):
    OTODOM = 'OTO'
    GUMTREE = 'GT'
    OLX = 'OLX'
    DOMIPORTA = "DP"
    MORIZON = "MZN"
    WAW_NIERUCHOMOSCI = "WAW_N"
    ADA = "ADA"
    GRATKA = "GTK"
    ADRESOWO = "ADS"
    OKOLICA = "OKO"


source_to_name = {
    Source.GUMTREE: 'gumtree'
}


class Location(models.Model):
    city = models.CharField(max_length=50, null=True)
    # e.g "ulica Marszałkowska"
    full_name = models.CharField(max_length=80, null=True)
    # e.g. przy "ul. Marszałkowskiej"
    by_name = models.CharField(max_length=80, null=True)
    # e.g. ul. Marszałkowska
    short_name = models.CharField(max_length=80, null=True)
    # list of districts e.g "Śródmieście, Wola" - not "srodmiescie, wola"
    districts_local_names = models.CharField(max_length=100, null=True)
    # From google api response, see https://developers.google.com/maps/documentation/geocoding/overview
    geolocation_data = jsonfield.JSONField(null=True)

    lat = models.FloatField(null=True)
    lng = models.FloatField(null=True)
    location_types = models.TextField(max_length=100, null=True)

    # ne = north east
    ne_lat = models.FloatField(null=True)
    ne_lng = models.FloatField(null=True)
    # sw = south west
    sw_lat = models.FloatField(null=True)
    sw_lng = models.FloatField(null=True)

    def is_type(self, location_type):
        return location_type in set(self.location_types.split(','))


class SearchArea(models.Model):
    name = models.CharField(max_length=80)
    # list of float pairs (lng, lat) (order is important)
    points = jsonfield.JSONField(null=True)


class BaseFlatInfo(models.Model):
    size_m2 = models.FloatField(null=True)
    city = models.CharField(max_length=50, null=True)
    district = models.CharField(max_length=50, null=True)

    class Meta:
        abstract = True


class PostHash(models.Model):
    source = models.CharField(max_length=6, choices=Source.choices)
    post_hash = models.CharField(max_length=64, unique=True)


class CrawlingLog(models.Model):
    source = models.CharField(max_length=6, choices=Source.choices)
    # Used to differentiate between different query urls on the same source
    crawl_id = models.CharField(max_length=200)
    # Crawled all posts posted on this date in the given source.
    date_fully_crawled = models.DateField()
    created = models.DateTimeField(auto_now_add=True)


class Flat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    original_post = models.ForeignKey('FlatPost', on_delete=models.PROTECT, related_name='+')
    min_price = models.IntegerField(null=True)
    created = models.DateTimeField(auto_now_add=True)

    rejected = models.BooleanField(default=False)
    starred = models.BooleanField(default=False)
    hearted = models.BooleanField(default=False)
    marked_as_duplicate = models.BooleanField(default=False)

    @property
    def last_post(self):
        return self.flatpost_set.filter(
            is_broken=False, expired=False
        ).order_by('dt_posted').last()

    @property
    def dt_posted(self):
        return self.original_post.dt_posted

    @property
    def date_added(self):
        return str(self.original_post.dt_posted.date())

    @property
    def url(self):
        return self.last_post.url

    @property
    def price(self):
        return self.last_post.price

    @property
    def thumbnail_image(self):
        return base64.b64encode(self.original_post.thumbnail).decode('utf-8')

    @property
    def photos(self):
        return [
            base64.b64encode(photo).decode('utf-8') for photo in self.original_post.photos_bytes.split(IMG_BYTES_DELIM)
        ]

    @property
    def size_m2(self):
        return self.original_post.size_m2

    @property
    def heading(self):
        return self.original_post.heading

    @property
    def title_q(self):
        source = source_to_name.get(self.original_post.source, '')
        return parse.quote(f'{source} "{self.heading}"')

    @property
    def desc(self):
        return self.original_post.desc

    @property
    def district(self):
        return self.original_post.district

    @property
    def keywords(self):
        if self.original_post.keywords is None:
            return ''
        return ', '.join(self.original_post.keywords.split(','))

    @property
    def location_names(self):
        return ', '.join(loc.short_name for loc in self.original_post.locations.all())

    @property
    def location_score(self):
        loc_num = self.original_post.locations.count()
        if loc_num == 0:
            return 0.00001
        return sum(x[1] for x in self.original_post.area_scores or []) / loc_num

    @property
    def location_color(self):
        if self.location_score == 0:
            return "red"
        elif self.location_score < 0.001:
            return "orange"

        if self.original_post.areas.filter(name=AREA_STARY_MOKOTOW).count() > 0:
            return "green"
        return "black"

    def rate(self, rating_type: str, is_ticked: bool):
        logger.debug(f"Rate flat: {self.id}, type: {rating_type}, ticked: {is_ticked}")
        # if we tick one true, others should turn to False
        if is_ticked:
            self.hearted = False
            self.starred = False
            self.rejected = False

        if rating_type == 'heart':
            self.hearted = is_ticked
        elif rating_type == 'star':
            self.starred = is_ticked
        elif rating_type == 'reject':
            self.rejected = is_ticked
        else:
            return
        self.save()


class FlatPost(BaseFlatInfo):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    flat = models.ForeignKey(Flat, on_delete=models.SET_NULL, blank=True, null=True)
    source = models.CharField(max_length=6, choices=Source.choices)
    url = models.URLField(max_length=300, null=True)

    thumbnail_url = models.URLField(max_length=300, null=True)
    thumbnail = models.BinaryField(null=True)

    price = models.IntegerField(null=True)
    heading = models.CharField(max_length=200, null=True)
    desc = models.TextField(null=True)
    photos_bytes = models.BinaryField(null=True)

    dt_posted = models.DateTimeField('date posted', null=True)

    locations = models.ManyToManyField(Location)
    tried_to_extract_locations = models.BooleanField(default=False)
    areas = models.ManyToManyField(SearchArea)
    area_scores = jsonfield.JSONField(null=True)

    has_balcony = models.BooleanField(null=True)
    info_dict_json = models.TextField(null=True)
    keywords = models.TextField(null=True)

    details_added = models.BooleanField(default=False)

    is_original_post = models.BooleanField(default=False)
    matched_by = models.CharField(max_length=100, null=True)

    expired = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    post_soup = models.BinaryField(null=True)
    post_detailed_soup = models.BinaryField(null=True)
    post_hash = models.CharField(max_length=64)
    is_broken = models.BooleanField(default=False)
    exception_str = models.TextField(null=True)

    @property
    def thumbnail_image(self):
        return base64.b64encode(self.thumbnail).decode('utf-8')

    @property
    def images(self):
        return bytes_to_images(self.photos_bytes)

    def __str__(self):
        if self.heading:
            return f"{self.heading[:100]}, id={self.id}"
        else:
            return f"id={self.id}"
        # url = textwrap.TextWrapper(
        #     width=100,
        #     initial_indent='\t',
        #     subsequent_indent='\t'
        # ).fill(text=self.url)
        # return f"\n\t{self.heading[:100]}\n{url}\n\t id: {self.id}"


class MatchingFlatPostGroup(models.Model):
    group_id_hash = models.TextField()
    posts = models.ManyToManyField(FlatPost)


class ImageMatch(models.Model):
    post_1 = models.ForeignKey(
        FlatPost, on_delete=models.SET_NULL, blank=True, null=True, related_name='img_match_1'
    )
    # Position of image on decompressed post_1.photos_bytes list, None means thumbnail
    img_pos_1 = models.IntegerField(null=True)

    post_2 = models.ForeignKey(
        FlatPost, on_delete=models.SET_NULL, blank=True, null=True, related_name='img_match_2'
    )
    # Position of image on decompressed post_2.photos_bytes list, None means thumbnail
    img_pos_2 = models.IntegerField(null=True)

    num_comparers_confirmed = models.IntegerField(null=True)
    num_comparers_maybe_matched = models.IntegerField(null=True)
    avg_score = models.FloatField(null=True)

    # Dict: comparer_id: comparer_score
    details_json = models.TextField(null=True)
    created = models.DateTimeField(auto_now_add=True)
