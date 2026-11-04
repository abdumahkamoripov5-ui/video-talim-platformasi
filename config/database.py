"""Parse managed PostgreSQL URLs without logging credentials."""
from urllib.parse import parse_qs, unquote, urlsplit
from django.core.exceptions import ImproperlyConfigured


def database_from_url(value):
    parsed = urlsplit(value)
    if parsed.scheme not in {'postgres', 'postgresql'} or not parsed.hostname or not parsed.path.strip('/'):
        raise ImproperlyConfigured('DATABASE_URL must be a PostgreSQL connection URL')
    query = parse_qs(parsed.query)
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': unquote(parsed.path.lstrip('/')),
        'USER': unquote(parsed.username or ''),
        'PASSWORD': unquote(parsed.password or ''),
        'HOST': parsed.hostname,
        'PORT': parsed.port or 5432,
        'CONN_MAX_AGE': 0,
        'CONN_HEALTH_CHECKS': True,
        'DISABLE_SERVER_SIDE_CURSORS': True,
        'OPTIONS': {'sslmode': query.get('sslmode', ['require'])[0], 'connect_timeout': 10},
    }
