from django.conf import settings
from django.core.paginator import Paginator
from .models import Post


def page_pagik(request, list_objects: list[Post]):
    """
    Паджик (паджинатор), который вернет страницу.
    """
    paginator = Paginator(list_objects, settings.COUNT_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
