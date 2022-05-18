from rest_framework.pagination import PageNumberPagination as BPNG


class PageNumberPagination(BPNG):
    page_size_query_param = 'size'
    max_page_size = 100
