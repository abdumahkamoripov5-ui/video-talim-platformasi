from datetime import timedelta

from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Permission
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from payments.models import Payment
from users.models import User


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AdminWorkspaceTests(TestCase):
    password = 'Forest!learning-7294'

    def setUp(self):
        self.admin = User.objects.create_superuser('owner@example.com', self.password, full_name='Platform Owner')
        self.client.force_login(self.admin)

    def account_data(self, **changes):
        data = {'email': self.admin.email, 'full_name': self.admin.full_name,
                'current_password': self.password, 'new_password1': '', 'new_password2': ''}
        return {**data, **changes}

    def test_dashboard_uses_paid_date_and_selected_period(self):
        payment = Payment.objects.create(user=self.admin, provider='payme', status='paid',
                                        amount=25000, paid_at=timezone.now())
        old = Payment.objects.create(user=self.admin, provider='click', status='paid',
                                    amount=8000, paid_at=timezone.now() - timedelta(days=40))
        response = self.client.get('/admin/?period=7')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/dashboard.html')
        self.assertEqual(response.context['revenue_period'], payment.amount)
        self.assertEqual(response.context['revenue_total'], payment.amount + old.amount)
        self.assertEqual(len(response.context['chart_data']), 7)
        self.assertContains(response, '/admin/account/')

    def test_invalid_period_uses_default(self):
        self.assertEqual(self.client.get('/admin/?period=huge').context['days'], 30)

    def test_staff_without_permissions_does_not_see_private_statistics(self):
        staff = User.objects.create_user('staff@example.com', self.password, is_staff=True)
        self.client.force_login(staff)
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('recent_payments', response.context)
        self.assertNotContains(response, self.admin.email)
        staff.user_permissions.add(Permission.objects.get(codename='view_course'))
        response = self.client.get('/admin/')
        self.assertIn('total_courses', response.context)
        self.assertNotIn('top_courses', response.context)

    def test_anonymous_and_student_cannot_edit_admin_account(self):
        self.client.logout()
        self.assertEqual(self.client.get('/admin/account/').status_code, 302)
        student = User.objects.create_user('student@example.com', self.password)
        self.client.force_login(student)
        self.assertEqual(self.client.post('/admin/account/', self.account_data()).status_code, 302)

    def test_current_password_is_required_and_changes_are_atomic(self):
        response = self.client.post('/admin/account/', self.account_data(
            current_password='incorrect', email='new@example.com'))
        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.email, 'owner@example.com')
        self.assertContains(response, 'Joriy parol noto‘g‘ri.')

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user('taken@example.com', self.password)
        response = self.client.post('/admin/account/', self.account_data(email='TAKEN@example.com'))
        self.assertContains(response, 'Bu email boshqa akkauntda ishlatilgan.')
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.email, 'owner@example.com')

    def test_weak_or_mismatched_password_does_not_save_email(self):
        for first, second in [('12345678', '12345678'), ('Strong!894711', 'different')]:
            response = self.client.post('/admin/account/', self.account_data(
                email='new@example.com', new_password1=first, new_password2=second))
            self.assertEqual(response.status_code, 200)
            self.admin.refresh_from_db()
            self.assertEqual(self.admin.email, 'owner@example.com')

    def test_email_and_password_change_preserves_current_session_and_invalidates_other(self):
        other = Client()
        other.force_login(self.admin)
        response = self.client.post('/admin/account/', self.account_data(
            email='new@example.com', new_password1='NewForest!72948', new_password2='NewForest!72948'))
        self.assertRedirects(response, '/admin/account/')
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.email, 'new@example.com')
        self.assertTrue(self.admin.check_password('NewForest!72948'))
        self.assertEqual(self.client.get('/admin/').status_code, 200)
        self.assertEqual(other.get('/admin/').status_code, 302)
        self.assertTrue(LogEntry.objects.filter(user=self.admin).exists())
        self.assertFalse(self.client.login(email='owner@example.com', password=self.password))
        self.assertTrue(self.client.login(email='new@example.com', password='NewForest!72948'))

    def test_email_only_change_preserves_password(self):
        response = self.client.post('/admin/account/', self.account_data(email='new@example.com'))
        self.assertEqual(response.status_code, 302)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password(self.password))

    def test_account_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post('/admin/account/', self.account_data()).status_code, 403)
