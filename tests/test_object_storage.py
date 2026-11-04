import io
from unittest.mock import patch, MagicMock
from urllib.parse import parse_qs, urlsplit

from botocore.exceptions import ClientError
from django.test import TestCase, SimpleTestCase, override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from courses.models import Course, Lesson, LessonAttachment
from users.models import User
from videos.models import MediaUpload, Video
from videos.object_storage import client, signed_download


@override_settings(OBJECT_STORAGE_ENABLED=True, MEDIA_BUCKET='private-media',
                   AWS_ENDPOINT_URL_S3='https://storage.example', AWS_ACCESS_KEY_ID='test-key',
                   AWS_SECRET_ACCESS_KEY='test-secret', AWS_REGION='us-east-2')
class SigningTests(SimpleTestCase):
    def test_private_download_uses_path_style_and_short_lived_signature(self):
        url = signed_download('uploads/video/lesson.mp4')
        self.assertEqual(urlsplit(url).path, '/private-media/uploads/video/lesson.mp4')
        query = parse_qs(urlsplit(url).query)
        self.assertIn('X-Amz-Signature', query)
        self.assertEqual(query['X-Amz-Expires'], ['1800'])

    def test_upload_signature_binds_size_and_type(self):
        url = client().generate_presigned_url('put_object', Params={
            'Bucket': 'private-media', 'Key': 'pending/test.mp4',
            'ContentType': 'video/mp4', 'ContentLength': 100,
        }, ExpiresIn=3600)
        headers = parse_qs(urlsplit(url).query)['X-Amz-SignedHeaders'][0]
        self.assertIn('content-length', headers)
        self.assertIn('content-type', headers)


@override_settings(OBJECT_STORAGE_ENABLED=True, PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DirectUploadTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin@example.com', 'test-password', full_name='Admin')
        self.student = User.objects.create_user('student@example.com', 'test-password', full_name='Student')
        self.course = Course.objects.create(title='Kurs', slug='kurs', is_published=True)
        self.lesson = Lesson.objects.create(course=self.course, title='Dars', is_published=True)
        self.client.force_login(self.admin)
        self.storage = MagicMock()
        self.storage.generate_presigned_url.return_value = 'https://storage.example/put?signed=1'
        self.mock_client = patch('videos.direct_upload.client', return_value=self.storage)
        self.mock_client.start()
        self.addCleanup(self.mock_client.stop)

    def start(self, kind='video', filename='lesson.mp4', size=100, **kwargs):
        return self.client.post('/admin/media-upload/start/', {
            'kind': kind, 'target_id': self.course.pk if kind == 'thumbnail' else self.lesson.pk,
            'filename': filename, 'size': size, 'duration_seconds': 120, **kwargs,
        }, content_type='application/json')

    def finish(self, ticket):
        return self.client.post(f'/admin/media-upload/{ticket.pk}/complete/', {}, content_type='application/json')

    def prepare(self, **kwargs):
        response = self.start(**kwargs)
        self.assertEqual(response.status_code, 200, response.content)
        ticket = MediaUpload.objects.get(pk=response.json()['id'])
        self.storage.head_object.return_value = {'ContentLength': ticket.size,
                                                'ContentType': ticket.content_type, 'ETag': 'etag'}
        return ticket

    def test_upload_page_and_admin_link(self):
        self.assertContains(self.client.get('/admin/media-upload/'), 'media-upload-form')
        self.assertContains(self.client.get('/admin/'), '/admin/media-upload/')

    def test_non_staff_cannot_get_upload_url(self):
        self.client.force_login(self.student)
        self.assertEqual(self.start().status_code, 302)
        self.assertFalse(MediaUpload.objects.exists())

    def test_csrf_required(self):
        from django.test import Client
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(self.admin)
        self.assertEqual(browser.post('/admin/media-upload/start/', {}, content_type='application/json').status_code, 403)

    def test_reject_paths_types_and_oversized_files(self):
        for name, size in [('../x.mp4', 10), ('x\\y.mp4', 10), ('bad.html', 10), ('x.mp4', 1024**3 + 1)]:
            with self.subTest(name=name, size=size):
                self.assertEqual(self.start(filename=name, size=size).status_code, 400)
        self.storage.generate_presigned_url.assert_not_called()

    def test_finalize_mp4_and_retry_is_idempotent(self):
        ticket = self.prepare()
        self.assertEqual(self.finish(ticket).status_code, 200)
        video = Video.objects.get(lesson=self.lesson)
        self.assertEqual(video.playback_format, 'mp4')
        self.assertEqual(video.status, 'ready')
        self.assertEqual(video.original_file.name, ticket.final_key)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.duration_seconds, 120)
        self.assertEqual(self.finish(ticket).status_code, 200)
        self.storage.copy_object.assert_called_once()
        self.assertNotEqual(ticket.final_key, ticket.staging_key)
        self.assertEqual(self.storage.copy_object.call_args.kwargs['CopySourceIfMatch'], 'etag')

    def test_wrong_size_is_not_published(self):
        ticket = self.prepare()
        self.storage.head_object.return_value['ContentLength'] = 99
        self.assertEqual(self.finish(ticket).status_code, 400)
        self.assertFalse(Video.objects.exists())

    def test_other_admin_cannot_finalize_ticket(self):
        ticket = self.prepare()
        other = User.objects.create_superuser('other@example.com', 'pw', full_name='Other')
        self.client.force_login(other)
        self.assertEqual(self.finish(ticket).status_code, 404)

    def test_expired_ticket_is_rejected(self):
        ticket = self.prepare()
        from datetime import timedelta
        MediaUpload.objects.filter(pk=ticket.pk).update(created_at=timezone.now() - timedelta(hours=3))
        self.assertEqual(self.finish(ticket).status_code, 400)

    def test_attachment_is_created_once(self):
        ticket = self.prepare(kind='attachment', filename='material.pdf', title='Qo‘llanma')
        self.assertEqual(self.finish(ticket).status_code, 200)
        self.assertEqual(self.finish(ticket).status_code, 200)
        self.assertEqual(LessonAttachment.objects.count(), 1)
        self.assertEqual(LessonAttachment.objects.get().file_type, 'pdf')

    def test_thumbnail_bytes_are_validated(self):
        ticket = self.prepare(kind='thumbnail', filename='photo.png')
        self.storage.get_object.return_value = {'Body': io.BytesIO(b'not-an-image')}
        self.assertEqual(self.finish(ticket).status_code, 400)
        self.storage.copy_object.assert_not_called()
        image = io.BytesIO()
        Image.new('RGB', (2, 2)).save(image, format='PNG')
        image.seek(0)
        self.storage.get_object.return_value = {'Body': image}
        self.assertEqual(self.finish(ticket).status_code, 200)
        self.course.refresh_from_db()
        self.assertEqual(self.course.thumbnail.name, ticket.final_key)

    def test_storage_failure_does_not_publish_video(self):
        ticket = self.prepare()
        self.storage.copy_object.side_effect = ClientError({'Error': {'Code': 'AccessDenied'}}, 'CopyObject')
        self.assertEqual(self.finish(ticket).status_code, 503)
        self.assertFalse(Video.objects.exists())

    def test_private_bucket_cors_configuration(self):
        self.storage.get_bucket_acl.return_value = {'Grants': []}
        result = self.client.post('/admin/media-upload/configure/', {}, content_type='application/json')
        self.assertEqual(result.status_code, 200)
        self.storage.put_bucket_cors.assert_called_once()

    def test_public_bucket_is_rejected(self):
        self.storage.get_bucket_acl.return_value = {'Grants': [{'Grantee': {'URI': 'http://acs.amazonaws.com/groups/global/AllUsers'}}]}
        result = self.client.post('/admin/media-upload/configure/', {}, content_type='application/json')
        self.assertEqual(result.status_code, 400)
        self.storage.put_bucket_cors.assert_not_called()
        self.assertEqual(self.start().status_code, 400)
        self.storage.generate_presigned_url.assert_not_called()

    @override_settings(OBJECT_STORAGE_ENABLED=False)
    def test_disabled_storage_keeps_uploads_off(self):
        self.assertEqual(self.start().status_code, 503)
        self.assertFalse(MediaUpload.objects.exists())

    def test_mp4_requires_subscription_and_returns_signed_url(self):
        Video.objects.create(lesson=self.lesson, status='ready', playback_format='mp4', original_file='uploads/video/x.mp4')
        api = APIClient()
        login = api.post('/api/users/auth/login/', {'email': self.student.email,
            'password': 'test-password', 'device_id': 'storage-test-device'}, format='json')
        self.assertEqual(login.status_code, 200)
        api.credentials(HTTP_AUTHORIZATION='Bearer ' + login.data['access'])
        endpoint = f'/api/courses/lessons/{self.lesson.pk}/video-url/'
        self.assertEqual(api.get(endpoint).status_code, 403)
        self.lesson.is_free_preview = True
        self.lesson.save()
        with patch('videos.object_storage.signed_download', return_value='https://storage.example/private?signature=x'):
            result = api.get(endpoint)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['format'], 'mp4')

    def test_attachment_requires_subscription_before_redirect(self):
        attachment = LessonAttachment.objects.create(lesson=self.lesson, title='PDF', file='uploads/attachment/x.pdf')
        api = APIClient()
        api.force_authenticate(self.student)
        endpoint = f'/api/videos/attachments/{attachment.pk}/'
        self.assertEqual(api.get(endpoint).status_code, 403)
        self.lesson.is_free_preview = True
        self.lesson.save()
        with patch('videos.object_storage.signed_download', return_value='https://storage.example/signed'):
            response = api.get(endpoint)
            signed = api.get(endpoint + '?download_url=1')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertEqual(signed.status_code, 200)
        self.assertEqual(signed.data['download_url'], 'https://storage.example/signed')
