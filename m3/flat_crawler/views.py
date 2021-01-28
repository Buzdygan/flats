from django.shortcuts import render
from django.views.generic.list import ListView

from flat_crawler.models import FlatPost
from flat_crawler.constants import SELECTED_DISTRICTS

class FlatPostView(ListView):
    model = FlatPost
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_queryset(self):
        queryset = FlatPost.objects.filter(
            district__in=SELECTED_DISTRICTS
        )
        return queryset
