from django.http import JsonResponse


class VercelUploadGuard:
    """Reject uploads until persistent storage and a video worker are connected."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in {'POST', 'PUT', 'PATCH'} and request.FILES:
            return JsonResponse({
                'detail': 'Fayl yuklash hali ulanmagan. Doimiy fayl saqlash va video qayta ishlash xizmatini sozlang.'
            }, status=503)
        return self.get_response(request)
