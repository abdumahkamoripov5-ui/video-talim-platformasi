from rest_framework.filters import OrderingFilter

class CatalogOrderingFilter(OrderingFilter):
    def filter_queryset(self, request, queryset, view):
        if request.query_params.get('ordering') in {'popular', 'rating'}:
            return queryset
        return super().filter_queryset(request, queryset, view)
