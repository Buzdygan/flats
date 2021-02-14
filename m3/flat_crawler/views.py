
import django_filters
from django.shortcuts import render
from django.views.generic.list import ListView
from django.http import JsonResponse
from django.db.models import Count

from rest_framework.generics import ListAPIView
from flat_crawler.serializers import FlatSerializers
from flat_crawler.pagination import StandardResultsSetPagination

from flat_crawler.models import Flat, FlatPost
from flat_crawler.constants import SELECTED_DISTRICTS, DEVELOPER_KEY


def FlatList(request):
    return render(request, 'flatlist.html', {})

class FlatView(ListAPIView):
    pagination_class = StandardResultsSetPagination
    serializer_class = FlatSerializers

    def get_queryset(self):
        show_rejected = self.request.query_params.get('show_rejected', None)
        show_hearted = self.request.query_params.get('show_hearted', None)
        show_starred = self.request.query_params.get('show_starred', None)
        show_unseen = self.request.query_params.get('show_unseen', None)
        district = self.request.query_params.get('district', None)
        sort_by = self.request.query_params.get('sort_by', None)
        min_size = self.request.query_params.get('min_size', None)
        max_size = self.request.query_params.get('max_size', None)
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)

        posts = FlatPost.objects.annotate(
            num_areas=Count('areas'),
            num_locations=Count('locations')
        ).exclude(num_locations__gt=0, num_areas=0)

        posts = posts.exclude(keywords__contains=DEVELOPER_KEY)

        queryset = Flat.objects.filter(
            original_post__district__in=SELECTED_DISTRICTS,
            original_post__in=posts
        )

        if not show_rejected == 'true':
            queryset = queryset.filter(rejected=False)
        if not show_hearted == 'true':
            queryset = queryset.filter(hearted=False)
        if not show_starred == 'true':
            queryset = queryset.filter(starred=False)
        if not show_unseen == 'true':
            queryset = queryset.exclude(starred=False, hearted=False, rejected=False)
        if district:
            queryset = queryset.filter(original_post__district=district)
        if min_size:
            queryset = queryset.filter(original_post__size_m2__gte=int(min_size))
        if max_size:
            queryset = queryset.filter(original_post__size_m2__lte=int(max_size))
        if min_price:
            queryset = queryset.filter(min_price__gte=int(min_price))
        if max_price:
            queryset = queryset.filter(min_price__lte=int(max_price))

        if sort_by == 'price':
            queryset = queryset.order_by('min_price')
        elif sort_by == 'dt_posted':
            queryset = queryset.order_by('-original_post__dt_posted')
        else:
            queryset = queryset.order_by('-original_post__dt_posted')
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
        if flat_id and rating_type and is_ticked:
            flat = Flat.objects.get(id=flat_id)
            flat.rate(rating_type=rating_type, is_ticked=is_ticked == "true")
        return JsonResponse({}, status=200)

        