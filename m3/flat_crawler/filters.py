from flat_crawler.models import FlatPost
import django_filters


class FlatFilter(django_filters.FilterSet):
    class Meta:
        model = FlatPost
        fields = ['district']
