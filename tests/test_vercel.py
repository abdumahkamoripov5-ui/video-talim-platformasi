from unittest.mock import patch
from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import OperationalError
from django.http import HttpResponse
from django.test import SimpleTestCase, TestCase, RequestFactory
from config.database import database_from_url
from config.middleware import VercelUploadGuard


class DatabaseURLTests(SimpleTestCase):
    def test_managed_pooler_url(self):
        db = database_from_url('postgresql://user:p%40ss@pool.example/db?sslmode=require')
        self.assertEqual(db['PASSWORD'], 'p@ss')
        self.assertEqual(db['HOST'], 'pool.example')
        self.assertEqual(db['OPTIONS']['sslmode'], 'require')
        self.assertEqual(db['CONN_MAX_AGE'], 0)
        self.assertTrue(db['DISABLE_SERVER_SIDE_CURSORS'])

    def test_no_sqlite_or_missing_database(self):
        for url in ['sqlite:///local.db', 'postgresql://host/', 'postgresql:///db']:
            with self.subTest(url=url), self.assertRaises(ImproperlyConfigured):
                database_from_url(url)

    def test_uploads_rejected_but_regular_forms_work(self):
        guard = VercelUploadGuard(lambda request: HttpResponse('ok'))
        factory = RequestFactory()
        upload = factory.post('/admin/', {'file': SimpleUploadedFile('test.txt', b'data')})
        self.assertEqual(guard(upload).status_code, 503)
        self.assertEqual(guard(factory.post('/admin/login/', {'username': 'test'})).status_code, 200)


class HealthTests(TestCase):
    def test_database_health(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_database_failure_is_not_exposed(self):
        with patch('config.health.connection.cursor', side_effect=OperationalError('secret-password')):
            response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b'secret-password', response.content)
