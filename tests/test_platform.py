import base64
import hashlib
import tempfile
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient
from users.models import User, UserDevice, VideoProgress
from courses.models import Course, Lesson, LessonAttachment, Enrollment
from payments.models import Tariff, Payment
from videos.models import Video
from quizzes.models import Quiz, QuizQuestion, Choice
from interactions.models import Question, LessonComment


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PlatformTests(TestCase):
    def setUp(self):
        cache.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.media = override_settings(MEDIA_ROOT=Path(self.tmp.name))
        self.media.enable(); self.addCleanup(self.media.disable)
        self.user = User.objects.create_user('student@example.com', 'Secure123!hello', full_name='Talaba')
        self.course = Course.objects.create(title='Python', slug='python', description='Test', is_published=True)
        self.lesson = Lesson.objects.create(course=self.course, title='Dars 1', is_published=True, duration_seconds=120)
        self.free = Lesson.objects.create(course=self.course, title='Bepul dars', is_published=True, is_free_preview=True, duration_seconds=100)
        self.tariff = Tariff.objects.create(name='30 kun', price=99000, duration_days=30)
        self.client = APIClient()

    def login(self, device='device-0001', client=None):
        client = client or self.client
        result = client.post('/api/users/auth/login/', {'email': self.user.email, 'password': 'Secure123!hello', 'device_id': device}, format='json')
        if result.status_code == 200:
            client.credentials(HTTP_AUTHORIZATION='Bearer ' + result.data['access'])
        return result

    def subscribe(self):
        self.user.subscription_end = timezone.now() + timedelta(days=30)
        self.user.save()

    def video(self):
        root = Path(self.tmp.name) / 'videos/hls' / str(self.lesson.pk)
        (root / '360p').mkdir(parents=True)
        (root / 'master.m3u8').write_text('#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360\n360p/index.m3u8\n')
        (root / '360p/index.m3u8').write_text('#EXTM3U\n#EXTINF:6,\nseg_000.ts\n')
        (root / '360p/seg_000.ts').write_bytes(b'segment')
        Video.objects.create(lesson=self.lesson, status='ready', hls_path=f'videos/hls/{self.lesson.pk}')

    def payment(self, provider='payme'):
        return Payment.objects.create(user=self.user, tariff=self.tariff, provider=provider, amount=self.tariff.price)

    def test_public_catalog(self):
        self.assertEqual(self.client.get('/api/courses/').status_code, 200)
        self.assertEqual(self.client.get('/api/courses/python/').data['total_lessons'], 2)

    def test_unpublished_course_hidden(self):
        self.course.is_published = False; self.course.save()
        self.assertEqual(self.client.get('/api/courses/python/').status_code, 404)
        self.login(); self.subscribe()
        self.assertEqual(self.client.get(f'/api/courses/lessons/{self.lesson.pk}/').status_code, 404)

    def test_third_device_login_is_rejected(self):
        self.assertEqual(self.login('device-0001').status_code, 200)
        self.assertEqual(self.login('device-0002').status_code, 200)
        self.assertEqual(self.login('device-0003').status_code, 403)
        self.assertEqual(self.user.devices.count(), 2)

    def test_same_device_relogin_allowed(self):
        self.login(); self.assertEqual(self.login().status_code, 200)
        self.assertEqual(self.user.devices.count(), 1)

    def test_login_requires_device(self):
        self.assertEqual(self.client.post('/api/users/auth/login/', {'email': self.user.email, 'password': 'Secure123!hello'}, format='json').status_code, 400)
        self.assertEqual(self.user.devices.count(), 0)

    def test_register_device_is_atomic(self):
        res = self.client.post('/api/users/auth/register/', {'email':'new@example.com', 'full_name':'New', 'password':'Secure123!hello','password2':'Secure123!hello'}, format='json')
        self.assertEqual(res.status_code,400)
        self.assertFalse(User.objects.filter(email='new@example.com').exists())

    def test_registration_creates_bound_token(self):
        res = self.client.post('/api/users/auth/register/', {'email':'new@example.com', 'full_name':'New', 'password':'Secure123!hello','password2':'Secure123!hello', 'device_id':'registration-device'}, format='json')
        self.assertEqual(res.status_code,201)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+res.data['access'])
        self.assertEqual(self.client.get('/api/users/profile/').status_code,200)

    def test_weak_password_rejected(self):
        res = self.client.post('/api/users/auth/register/', {'email':'new@example.com', 'full_name':'New', 'password':'12345678','password2':'12345678','device_id':'registration-device'}, format='json')
        self.assertEqual(res.status_code,400)

    def test_deleted_device_revokes_access_and_refresh(self):
        res = self.login()
        self.user.devices.all().delete()
        self.assertEqual(self.client.get('/api/users/profile/').status_code,401)
        self.assertEqual(APIClient().post('/api/users/auth/refresh/', {'refresh':res.data['refresh']}, format='json').status_code,401)

    def test_refresh_rotation(self):
        token = self.login().data['refresh']
        client = APIClient()
        res = client.post('/api/users/auth/refresh/', {'refresh':token}, format='json')
        self.assertEqual(res.status_code,200)
        self.assertNotEqual(res.data['refresh'],token)
        self.assertEqual(client.post('/api/users/auth/refresh/', {'refresh':token}, format='json').status_code,401)

    def test_logout_revokes_device(self):
        self.login()
        self.assertEqual(self.client.post('/api/users/auth/logout/').status_code,200)
        self.assertEqual(self.client.get('/api/users/profile/').status_code,401)

    def test_expired_subscription_blocks_lesson(self):
        self.login()
        self.user.subscription_end=timezone.now()-timedelta(seconds=1); self.user.save()
        self.assertEqual(self.client.get(f'/api/courses/lessons/{self.lesson.pk}/').status_code,403)
        self.assertEqual(self.client.get(f'/api/courses/lessons/{self.free.pk}/').status_code,200)

    def test_resume_position_and_completed_stays_completed(self):
        self.login(); self.subscribe(); self.video()
        res=self.client.post('/api/users/progress/', {'lesson':self.lesson.pk, 'watched_seconds':110},format='json')
        self.assertEqual(res.status_code,200); self.assertTrue(res.data['is_completed'])
        res=self.client.post('/api/users/progress/', {'lesson':self.lesson.pk, 'watched_seconds':40},format='json')
        self.assertTrue(res.data['is_completed'])
        self.assertEqual(self.client.get(f'/api/courses/lessons/{self.lesson.pk}/video-url/').data['resume_at'],40)
        self.assertEqual(Enrollment.objects.get(user=self.user,course=self.course).get_progress(),50)

    def test_progress_validates_input(self):
        self.login(); self.subscribe()
        for value in [-1, 'invalid']:
            self.assertEqual(self.client.post('/api/users/progress/', {'lesson':self.lesson.pk,'watched_seconds':value},format='json').status_code,400)
        self.assertEqual(self.client.post('/api/users/progress/', {'lesson':999999,'watched_seconds':1},format='json').status_code,400)

    def test_progress_requires_subscription(self):
        self.login()
        self.assertEqual(self.client.post('/api/users/progress/', {'lesson':self.lesson.pk,'watched_seconds':100},format='json').status_code,403)

    def test_unknown_duration_does_not_allow_forged_completion(self):
        self.login(); self.subscribe(); self.lesson.duration_seconds=0; self.lesson.save()
        res=self.client.post('/api/users/progress/', {'lesson':self.lesson.pk,'watched_seconds':999999,'is_completed':True},format='json')
        self.assertFalse(res.data['is_completed'])

    def test_video_playlist_and_segments_are_signed(self):
        self.login(); self.subscribe(); self.video()
        url=self.client.get(f'/api/courses/lessons/{self.lesson.pk}/video-url/').data['url']
        res=self.client.get(url)
        self.assertEqual(res.status_code,200)
        variant=[l for l in res.content.decode().splitlines() if not l.startswith('#')][0]
        variant_url=url.split('master.m3u8')[0]+variant
        res=self.client.get(variant_url)
        self.assertEqual(res.status_code,200)
        segment=[l for l in res.content.decode().splitlines() if not l.startswith('#')][0]
        res=self.client.get(variant_url.split('index.m3u8')[0]+segment)
        self.assertEqual(res.status_code,200)
        self.assertEqual(b''.join(res.streaming_content), b'segment')

    def test_video_shared_link_is_rejected(self):
        self.login(); self.subscribe(); self.video()
        url=self.client.get(f'/api/courses/lessons/{self.lesson.pk}/video-url/').data['url']
        self.assertEqual(APIClient().get(url).status_code,403)
        other=APIClient();self.login('device-0002',other)
        self.assertEqual(other.get(url).status_code,403)

    def test_video_token_expiration(self):
        self.login();self.subscribe();self.video()
        url=self.client.get(f'/api/courses/lessons/{self.lesson.pk}/video-url/').data['url']
        with patch('django.core.signing.time.time', return_value=timezone.now().timestamp()+1900):
            self.assertEqual(self.client.get(url).status_code,403)

    def test_stream_cookie_works_without_authorization_header(self):
        self.login();self.subscribe();self.video()
        url=self.client.get(f'/api/courses/lessons/{self.lesson.pk}/video-url/').data['url']
        self.client.credentials()
        self.assertEqual(self.client.get(url).status_code,200)

    def test_stream_revoked_when_subscription_expires(self):
        self.login();self.subscribe();self.video()
        url=self.client.get(f'/api/courses/lessons/{self.lesson.pk}/video-url/').data['url']
        self.user.subscription_end=timezone.now()-timedelta(seconds=1);self.user.save()
        self.assertEqual(self.client.get(url).status_code,403)

    @override_settings(DEBUG=True)
    def test_raw_video_and_attachments_not_public(self):
        from videos.streaming import public_media
        from django.http import Http404
        from django.test import RequestFactory
        for path in ['videos/hls/1/master.m3u8','videos/originals/test.mp4','lessons/attachments/file.pdf','courses/evil.svg']:
            with self.assertRaises(Http404):public_media(RequestFactory().get('/'), path)

    def test_attachment_download_requires_subscription(self):
        from django.core.files.base import ContentFile
        obj=LessonAttachment.objects.create(lesson=self.lesson,title='PDF')
        obj.file.save('test.pdf',ContentFile(b'%PDF-1.4'),save=True)
        self.login()
        url=f'/api/videos/attachments/{obj.pk}/'
        self.assertEqual(self.client.get(url).status_code,403)
        self.subscribe()
        self.assertEqual(self.client.get(url).status_code,200)

    def test_subscription_activation_is_idempotent(self):
        payment=self.payment()
        self.assertTrue(payment.activate_subscription())
        self.user.refresh_from_db(); end=self.user.subscription_end
        self.assertFalse(payment.activate_subscription())
        self.user.refresh_from_db();self.assertEqual(end,self.user.subscription_end)

    def test_payment_extends_current_subscription(self):
        self.subscribe();end=self.user.subscription_end
        self.payment().activate_subscription();self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_end,end+timedelta(days=30))

    def test_payment_duration_is_snapshot(self):
        payment=self.payment();self.tariff.duration_days=365;self.tariff.save()
        payment.activate_subscription();self.user.refresh_from_db()
        self.assertAlmostEqual((self.user.subscription_end-timezone.now()).total_seconds()/86400,30,places=2)

    @override_settings(PAYME_MERCHANT_ID='', PAYME_SECRET='')
    def test_unconfigured_provider_returns_clear_error(self):
        self.login()
        res=self.client.post('/api/payments/create/',{'tariff_id':self.tariff.pk,'provider':'payme'},format='json')
        self.assertEqual(res.status_code,503);self.assertEqual(Payment.objects.count(),0)

    def test_webhooks_reject_forged_confirmation(self):
        payment=self.payment()
        self.client.post('/api/payments/webhook/payme/',{'method':'PerformTransaction','params':{'account':{'payment_id':str(payment.pk)}}},format='json')
        self.client.post('/api/payments/webhook/click/',{'merchant_trans_id':str(payment.pk),'error':0},format='json')
        payment.refresh_from_db();self.assertEqual(payment.status,'pending')

    @override_settings(PAYME_SECRET='test-secret')
    def test_payme_flow_and_duplicate_perform(self):
        payment=self.payment();client=APIClient()
        client.credentials(HTTP_AUTHORIZATION='Basic '+base64.b64encode(b'Paycom:test-secret').decode())
        def call(method,params):return client.post('/api/payments/webhook/payme/',{'id':1,'method':method,'params':params},format='json').data
        params={'account':{'payment_id':str(payment.pk)},'id':'external-1','amount':9900000,'time':int(timezone.now().timestamp()*1000)}
        self.assertTrue(call('CheckPerformTransaction',params)['result']['allow'])
        self.assertEqual(call('CreateTransaction',params)['result']['state'],1)
        self.assertEqual(call('PerformTransaction',{'id':'external-1'})['result']['state'],2)
        self.user.refresh_from_db();end=self.user.subscription_end
        call('PerformTransaction',{'id':'external-1'})
        self.user.refresh_from_db();self.assertEqual(self.user.subscription_end,end)

    @override_settings(PAYME_SECRET='test-secret')
    def test_payme_checks_amount(self):
        payment=self.payment();client=APIClient()
        client.credentials(HTTP_AUTHORIZATION='Basic '+base64.b64encode(b'Paycom:test-secret').decode())
        res=client.post('/api/payments/webhook/payme/',{'method':'CreateTransaction','params':{'account':{'payment_id':str(payment.pk)},'amount':1}},format='json')
        self.assertEqual(res.data['error']['code'],-31001)

    @override_settings(CLICK_SECRET='secret', CLICK_SERVICE_ID='123')
    def test_click_prepare_complete_signature(self):
        payment=self.payment('click');client=APIClient()
        def call(action,amount='99000.00'):
            data={'click_trans_id':'1234','service_id':'123','merchant_trans_id':str(payment.pk),'amount':amount,'action':action,'sign_time':'2026-11-03 12:00:00','error':'0'}
            raw='1234'+'123'+'secret'+str(payment.pk)
            if action=='1':data['merchant_prepare_id']=str(payment.pk);raw+=str(payment.pk)
            raw+=amount+action+data['sign_time'];data['sign_string']=hashlib.md5(raw.encode()).hexdigest()
            return client.post('/api/payments/webhook/click/',data,format='json')
        self.assertEqual(call('0').data['error'],0)
        self.assertEqual(call('1').data['error'],0)
        payment.refresh_from_db();self.assertEqual(payment.status,'paid')
        self.user.refresh_from_db();end=self.user.subscription_end
        self.assertEqual(call('1').data['error'],-4)
        self.user.refresh_from_db();self.assertEqual(end,self.user.subscription_end)

    @override_settings(UZUM_LOGIN='merchant',UZUM_PASSWORD='secret',UZUM_SERVICE_ID='123')
    def test_uzum_create_confirm(self):
        payment=self.payment('uzum');client=APIClient()
        client.credentials(HTTP_AUTHORIZATION='Basic '+base64.b64encode(b'merchant:secret').decode())
        data={'serviceId':123,'params':{'account':str(payment.pk)},'transId':'uzum-transaction','amount':9900000}
        self.assertEqual(client.post('/api/payments/webhook/uzum/create/',data,format='json').data['status'],'CREATED')
        self.assertEqual(client.post('/api/payments/webhook/uzum/confirm/',data,format='json').data['status'],'CONFIRMED')
        self.assertEqual(client.post('/api/payments/webhook/uzum/confirm/',data,format='json').data['status'],'CONFIRMED')
        self.user.refresh_from_db();self.assertAlmostEqual((self.user.subscription_end-timezone.now()).total_seconds()/86400,30,places=2)

    def test_comment_can_be_created_without_lesson_in_body(self):
        self.login()
        res=self.client.post(f'/api/interactions/lessons/{self.free.pk}/comments/',{'content':'Yaxshi dars'},format='json')
        self.assertEqual(res.status_code,201)

    def test_cross_lesson_comment_reply_rejected(self):
        self.login()
        comment=LessonComment.objects.create(user=self.user,lesson=self.lesson,content='Test')
        res=self.client.post(f'/api/interactions/lessons/{self.free.pk}/comments/',{'content':'Javob','parent':comment.pk},format='json')
        self.assertEqual(res.status_code,400)

    def test_invalid_review_rating_is_rejected(self):
        self.login()
        for rating in [0,6,'bad']:
            res=self.client.post(f'/api/interactions/courses/{self.course.pk}/reviews/',{'rating':rating},format='json')
            self.assertEqual(res.status_code,400)

    def test_cannot_delete_another_users_question(self):
        owner=User.objects.create_user('other@example.com','secret')
        question=Question.objects.create(user=owner,lesson=self.lesson,title='Test',content='Test')
        self.login()
        self.assertEqual(self.client.delete(f'/api/interactions/questions/{question.pk}/').status_code,403)

    def test_quiz_requires_subscription_and_handles_bad_answers(self):
        quiz=Quiz.objects.create(lesson=self.lesson,title='Test')
        question=QuizQuestion.objects.create(quiz=quiz,text='Test')
        Choice.objects.create(question=question,text='A',is_correct=True)
        self.login()
        url=f'/api/quizzes/lessons/{self.lesson.pk}/'
        self.assertEqual(self.client.get(url).status_code,403)
        self.subscribe()
        self.assertEqual(self.client.get(url).status_code,200)
        self.assertEqual(self.client.post(url+'submit/',{'answers':[]},format='json').status_code,400)
        self.assertEqual(self.client.post(url+'submit/',{'answers':{str(question.pk):'bad'}},format='json').status_code,400)

    def test_admin_dashboard_staff_only(self):
        self.assertEqual(self.client.get('/admin/dashboard/').status_code,302)
        self.user.is_staff=True;self.user.save();self.client.force_login(self.user)
        self.assertEqual(self.client.get('/admin/dashboard/').status_code,200)

    def test_catalog_guest_query_count_is_bounded(self):
        for index in range(15):
            Course.objects.create(title=f'Course {index}',slug=f'course-{index}',is_published=True)
        with self.assertNumQueries(2):
            response=self.client.get('/api/courses/')
            self.assertEqual(response.status_code,200)
            self.assertEqual(len(response.data['results']),16)

    @override_settings(PAYME_SECRET='test-secret')
    def test_payme_rejects_malformed_json(self):
        client=APIClient();client.credentials(HTTP_AUTHORIZATION='Basic '+base64.b64encode(b'Paycom:test-secret').decode())
        self.assertEqual(client.post('/api/payments/webhook/payme/', [], format='json').status_code,400)
        result=client.post('/api/payments/webhook/payme/', {'method':'CreateTransaction','params':{'account':[]}}, format='json')
        self.assertEqual(result.data['error']['code'],-31050)
