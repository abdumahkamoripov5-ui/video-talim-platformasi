import logging
from django.db import connection, DatabaseError
from django.http import JsonResponse
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@require_GET
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except DatabaseError:
        logger.exception('Database health check failed')
        response = JsonResponse({'status': 'unavailable'}, status=503)
    else:
        response = JsonResponse({'status': 'ok'})
    response['Cache-Control'] = 'no-store'
    return response
