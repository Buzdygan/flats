import uuid

from django.db import models


THUBMNAIL_SIZE = (150, 100)


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


class BaseFlatInfo(models.Model):
    size_m2 = models.DecimalField(max_digits=7, decimal_places=2)
    city = models.CharField(max_length=50, null=True)
    district = models.CharField(max_length=50, null=True)
    sub_district = models.CharField(max_length=50, null=True)
    street = models.CharField(max_length=50, null=True)

    class Meta:
        abstract = True


class PostHash(models.Model):
    source = models.CharField(max_length=6, choices=Source.choices)
    post_hash = models.CharField(max_length=64, unique=True)


class Flat(BaseFlatInfo):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    min_price = models.IntegerField(null=True)
    recent_price = models.IntegerField(null=True)
    created = models.DateTimeField(auto_now_add=True)


class FlatPost(BaseFlatInfo):
    flat = models.ForeignKey(Flat, on_delete=models.SET_NULL, blank=True, null=True)
    source = models.CharField(max_length=6, choices=Source.choices)
    url = models.URLField(max_length=300)

    img_url = models.URLField(max_length=300, null=True)
    thumbnail = models.BinaryField(null=True)

    price = models.IntegerField()
    heading = models.CharField(max_length=200, null=True)
    desc = models.TextField(null=True)
    photos_signature_json = models.TextField(null=True)

    has_balcony = models.BooleanField(default=False)
    other_info = models.TextField(null=True)

    details_added = models.BooleanField(default=False)

    is_original_post = models.BooleanField(default=False)
    was_matched = models.BooleanField(default=False)

    expired = models.BooleanField(default=False)
    dt_posted = models.DateTimeField('date posted')
    created = models.DateTimeField(auto_now_add=True)

    post_soup = models.TextField(null=True)
    post_hash = models.CharField(max_length=64)

    def __repr__(self):
        return f"{self.heading}, url: {self.url}"
