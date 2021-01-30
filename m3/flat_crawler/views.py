
import django_filters
from django.shortcuts import render
from django.views.generic.list import ListView
from django.http import JsonResponse

from rest_framework.generics import ListAPIView
from flat_crawler.serializers import FlatSerializers
from flat_crawler.pagination import StandardResultsSetPagination

from flat_crawler.models import Flat, FlatPost
from flat_crawler.constants import SELECTED_DISTRICTS


# class FlatFilter(django_filters.FilterSet):
#     class Meta:
#         model = Flat
#         fields = ['original_post__size_m2']


# class FlatView(ListView):
#     model = Flat
#     paginate_by = 50

#     ordering_fields = ['original_post__size_m2']

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         return context

#     def get_queryset(self):
#         return Flat.objects.filter(
#             original_post__district__in=SELECTED_DISTRICTS
#         )


def FlatList(request):
    return render(request, 'flatlist.html', {})

class FlatView(ListAPIView):
    pagination_class = StandardResultsSetPagination
    serializer_class = FlatSerializers

    def get_queryset(self):
        queryset = Flat.objects.filter(
            original_post__district__in=SELECTED_DISTRICTS
        )
        district = self.request.query_params.get('district', None)
        sort_by = self.request.query_params.get('sort_by', None)
        if district:
            queryset = queryset.filter(original_post__district=district)
        if sort_by == 'price':
            queryset = queryset.order_by('min_price')
        return queryset


def get_districts(request):
    if request.method == 'GET' and request.is_ajax():
        data = {
            'districts': SELECTED_DISTRICTS
        }
        return JsonResponse(data, status=200)

        