
import django_filters
from django.shortcuts import render
from django.views.generic.list import ListView
from django.http import JsonResponse

from rest_framework.generics import ListAPIView
from flat_crawler.serializers import FlatSerializers
from flat_crawler.pagination import StandardResultsSetPagination

from flat_crawler.models import Flat, FlatPost
from flat_crawler.constants import SELECTED_DISTRICTS


def FlatList(request):
    return render(request, 'flatlist.html', {})

class FlatView(ListAPIView):
    pagination_class = StandardResultsSetPagination
    serializer_class = FlatSerializers

    def get_queryset(self):
        queryset = Flat.objects.filter(
            original_post__district__in=SELECTED_DISTRICTS
        )
        exclude_rejected = self.request.query_params.get('exclude_rejected', None)
        district = self.request.query_params.get('district', None)
        sort_by = self.request.query_params.get('sort_by', None)
        if exclude_rejected == 'true':
            queryset = queryset.filter(rejected=False)
        if district:
            queryset = queryset.filter(original_post__district=district)
        if sort_by == 'price':
            queryset = queryset.order_by('min_price')
        else:
            queryset = queryset.order_by('created')
        return queryset


def get_districts(request):
    if request.method == 'GET' and request.is_ajax():
        data = {
            'districts': SELECTED_DISTRICTS
        }
        return JsonResponse(data, status=200)


def update_flat(request):
    if request.method == 'GET' and request.is_ajax():
        flat_id = request.GET.get('flat_id')
        rating_type = request.GET.get('rating_type')
        is_ticked = request.GET.get('is_ticked')
        print(flat_id, rating_type, is_ticked)
        if flat_id and rating_type and is_ticked:
            flat = Flat.objects.get(id=flat_id)
            flat.rate(rating_type=rating_type, is_ticked=is_ticked == "true")
        return JsonResponse({}, status=200)

        