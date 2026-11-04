from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_safe


@require_safe
def frontend(request, path=''):
    # Unknown API/admin/media paths must never return the SPA shell.
    if path.split('/')[0] in {'api', 'admin', 'media', 'static'}:
        raise Http404
    return render(request, 'spa.html')


@require_safe
def public_asset(request, filename):
    # Only these public files may be served from the build directory.
    if filename not in {'manifest.json', 'sw.js', 'icon-192.svg', 'icon-512.svg'}:
        raise Http404
    target = settings.BASE_DIR / 'frontend' / 'dist' / filename
    if not target.is_file():
        raise Http404
    response = FileResponse(target.open('rb'))
    if filename == 'sw.js':
        response['Content-Type'] = 'application/javascript'
        response['Cache-Control'] = 'no-cache'
    return response
