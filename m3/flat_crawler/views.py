from django.shortcuts import render
from django.views.generic.list import ListView

from flat_crawler.models import Flat, FlatPost
from flat_crawler.constants import SELECTED_DISTRICTS


class FlatView(ListView):
    model = Flat
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_queryset(self):
        flat_ids = FlatPost.objects.filter(
            district__in=SELECTED_DISTRICTS,
            flat__isnull=False
        ).values_list('flat__id').distinct()
        return Flat.objects.filter(id__in=flat_ids)
