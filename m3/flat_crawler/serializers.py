from rest_framework import serializers
from flat_crawler.models import Flat


class FlatSerializers(serializers.ModelSerializer):
    class Meta:
        model = Flat
        fields = ('id', 'url', 'thumbnail_image', 'size_m2', 'min_price',
                  'heading', 'desc', 'district', 'rejected', 'starred', 'hearted', 'created',
                  'dt_posted', 'photos', 'location_names', 'location_color', 'keywords', 'date_added')