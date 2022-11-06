from django.conf import settings
from django.core.paginator import Paginator


def paginate(request, data_list):
    paginator = Paginator(data_list, settings.NUMBER_POST)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return page_obj
