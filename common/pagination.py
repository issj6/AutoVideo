from rest_framework.pagination import PageNumberPagination

from common.res import Res


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'

    # max_page_size = 100

    def get_paginated_response(self, data):
        return Res(200, 'ok', {
            'total': self.page.paginator.count,
            'current_page': self.page.number,
            'page_size': self.page_size,
            'results': data
        })
