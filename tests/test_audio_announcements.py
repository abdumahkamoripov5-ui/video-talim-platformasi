from django.test import TestCase
from rest_framework.test import APIClient
from courses.models import Course, Lesson
from notifications.models import Announcement
from videos.direct_upload import UploadRequest
from videos.models import Video


class AudioUploadTests(TestCase):
    def test_audio_kind_accepts_mp3_m4a_wav(self):
        for name, mime in [('lesson.mp3', 'audio/mpeg'), ('lesson.m4a', 'audio/mp4'), ('lesson.wav', 'audio/wav')]:
            s = UploadRequest(data={'kind': 'audio', 'target_id': 1, 'filename': name, 'size': 1000})
            self.assertTrue(s.is_valid(), s.errors)
            self.assertEqual(s.validated_data['content_type'], mime)

    def test_audio_kind_rejects_video_extension(self):
        s = UploadRequest(data={'kind': 'audio', 'target_id': 1, 'filename': 'lesson.mp4', 'size': 1000})
        self.assertFalse(s.is_valid())

    def test_video_kind_still_rejects_mp3(self):
        s = UploadRequest(data={'kind': 'video', 'target_id': 1, 'filename': 'lesson.mp3', 'size': 1000})
        self.assertFalse(s.is_valid())


class AnnouncementTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        Announcement.objects.create(title='Yangi kurs', body='Python kursi chiqdi', is_published=True)
        Announcement.objects.create(title='Qoralama', body='hali chiqmagan', is_published=False)

    def test_public_list_returns_only_published(self):
        response = self.client.get('/api/notifications/announcements/')
        self.assertEqual(response.status_code, 200)
        titles = [item['title'] for item in response.data]
        self.assertEqual(titles, ['Yangi kurs'])

    def test_announcement_list_is_capped(self):
        for i in range(8):
            Announcement.objects.create(title=f'E{i}', body='x', is_published=True)
        self.assertLessEqual(len(self.client.get('/api/notifications/announcements/').data), 5)


class AudioLessonUrlTests(TestCase):
    def test_video_url_reports_audio_media(self):
        from users.models import User
        from django.core.files.base import ContentFile
        from django.test import override_settings
        import tempfile
        from pathlib import Path
        from payments.models import Tariff
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        user = User.objects.create_user('aud@example.com', 'Secure123!hello', full_name='Aud')
        user.is_staff = False
        course = Course.objects.create(title='Musiqa', slug='musiqa', description='d', is_published=True)
        lesson = Lesson.objects.create(course=course, title='Audio dars', is_published=True, is_free_preview=True, duration_seconds=60)
        video = Video.objects.create(lesson=lesson, status='ready', playback_format='mp4', original_file='audio/lesson.mp3')
        self.assertTrue(video.original_file.name.endswith('.mp3'))
        client = APIClient()
        client.post('/api/users/auth/login/', {'email': 'aud@example.com', 'password': 'Secure123!hello', 'device_id': 'audio-device-01', 'device_name': 'PC'}, format='json')
        token = client.post('/api/users/auth/login/', {'email': 'aud@example.com', 'password': 'Secure123!hello', 'device_id': 'audio-device-01', 'device_name': 'PC'}, format='json').data['access']
        from django.test import override_settings as _o
        with _o(OBJECT_STORAGE_ENABLED=True):
            from unittest.mock import patch
            with patch('videos.object_storage.signed_download', return_value='https://storage.example/lesson.mp3'):
                response = client.get(f'/api/courses/lessons/{lesson.pk}/video-url/', HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['media'], 'audio')
