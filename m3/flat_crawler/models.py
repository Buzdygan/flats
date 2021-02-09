import uuid
import base64
import textwrap

import jsonfield
from django.db import models

from flat_crawler.utils.img_utils import bytes_to_images


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
    location_type = models.CharField(max_length=100, null=True)

    # ne = north east
    ne_lat = models.FloatField(null=True)
    ne_lng = models.FloatField(null=True)
    # sw = south west
    sw_lat = models.FloatField(null=True)
    sw_lng = models.FloatField(null=True)

    def get_names_for_matching(self):
        """ Return versions of location name for purpose of matching. Order is important as first
            element will be tried first, so it's better to put longer, more defining versions first.
            Return (name, max levenstein distance allowed)
        """
        names_with_dists = []
        names_with_dists.append((self.full_name, 0))
        names_with_dists.append((self.by_name, 0))
        names_with_dists.append((self.short_name, 0))

        # versions easier to match
        # names_with_dists.append((self.short_name.replace('ul.', '').replace('pl.', '').strip(), 0))
        # names_with_dists.append((self.by_name.replace('ul.', '').replace('pl.', '').strip(), 0))
        return names_with_dists


class BaseFlatInfo(models.Model):
    size_m2 = models.FloatField(null=True)
    city = models.CharField(max_length=50, null=True)
    district = models.CharField(max_length=50, null=True)
    locations = models.ManyToManyField(Location, null=True)

    class Meta:
        abstract = True


class PostHash(models.Model):
    source = models.CharField(max_length=6, choices=Source.choices)
    post_hash = models.CharField(max_length=64, unique=True)


class Flat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    original_post = models.ForeignKey('FlatPost', on_delete=models.PROTECT, related_name='+')
    min_price = models.IntegerField(null=True)
    created = models.DateTimeField(auto_now_add=True)

    @property
    def last_post(self):
        return self.flatpost_set.filter(
            is_broken=False, expired=False
        ).order_by('dt_posted').last()

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
    def size_m2(self):
        return self.original_post.size_m2

    @property
    def heading(self):
        return self.original_post.heading

    @property
    def desc(self):
        return self.original_post.desc

    @property
    def district(self):
        return self.original_post.district


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

    has_balcony = models.BooleanField(null=True)
    info_dict_json = models.TextField(null=True)

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
        url = textwrap.TextWrapper(
            width=100,
            initial_indent='\t',
            subsequent_indent='\t'
        ).fill(text=self.url)
        return f"\n\t{self.heading[:100]}\n{url}\n\t id: {self.id}"


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
