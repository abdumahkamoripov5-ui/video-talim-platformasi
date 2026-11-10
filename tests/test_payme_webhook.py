import base64
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from payments.models import Payment, Tariff
from users.models import User

SECRET = 'test-payme-secret'
AUTH = 'Basic ' + base64.b64encode(f'Paycom:{SECRET}'.encode()).decode()


@override_settings(PAYME_SECRET=SECRET, PAYME_MERCHANT_ID='merchant-test')
class PaymeWebhookFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('payer@example.com', 'Secure123!hello', full_name='Payer')
        self.tariff = Tariff.objects.create(name='30 kun', price=99000, duration_days=30)
        self.payment = Payment.objects.create(user=self.user, tariff=self.tariff, provider='payme', amount=self.tariff.price)
        self.amount = int(self.payment.amount * 100)

    def rpc(self, method, params, auth=AUTH, rid=1):
        headers = {'HTTP_AUTHORIZATION': auth} if auth else {}
        return self.client.post('/api/payments/webhook/payme/', {'jsonrpc': '2.0', 'id': rid, 'method': method, 'params': params}, format='json', **headers)

    def tx(self, tx_id='tx-001'):
        return {'id': tx_id, 'time': 1700000000000, 'amount': self.amount, 'account': {'payment_id': str(self.payment.pk)}}

    def test_rejects_missing_or_wrong_auth(self):
        self.assertEqual(self.rpc('CheckPerformTransaction', {'amount': self.amount, 'account': {'payment_id': str(self.payment.pk)}}, auth=None).json()['error']['code'], -32504)
        bad = 'Basic ' + base64.b64encode(b'Paycom:wrong').decode()
        self.assertEqual(self.rpc('CheckPerformTransaction', {'amount': self.amount, 'account': {'payment_id': str(self.payment.pk)}}, auth=bad).json()['error']['code'], -32504)

    def test_check_perform_allows_pending_order_with_correct_amount(self):
        res = self.rpc('CheckPerformTransaction', {'amount': self.amount, 'account': {'payment_id': str(self.payment.pk)}})
        self.assertEqual(res.json()['result'], {'allow': True})

    def test_wrong_amount_is_rejected(self):
        res = self.rpc('CheckPerformTransaction', {'amount': self.amount - 100, 'account': {'payment_id': str(self.payment.pk)}})
        self.assertEqual(res.json()['error']['code'], -31001)

    def test_full_payment_flow_activates_subscription_once(self):
        created = self.rpc('CreateTransaction', self.tx())
        self.assertEqual(created.json()['result']['state'], 1)
        performed = self.rpc('PerformTransaction', {'id': 'tx-001'})
        self.assertEqual(performed.json()['result']['state'], 2)
        self.payment.refresh_from_db(); self.user.refresh_from_db()
        self.assertEqual(self.payment.status, 'paid')
        self.assertIsNotNone(self.user.subscription_end)
        end_after_first = self.user.subscription_end
        again = self.rpc('PerformTransaction', {'id': 'tx-001'})
        self.assertEqual(again.json()['result']['state'], 2)
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_end, end_after_first)

    def test_cancel_after_paid_is_refused(self):
        self.rpc('CreateTransaction', self.tx())
        self.rpc('PerformTransaction', {'id': 'tx-001'})
        res = self.rpc('CancelTransaction', {'id': 'tx-001', 'reason': 3})
        self.assertEqual(res.json()['error']['code'], -31007)

    def test_cancel_pending_transaction_is_allowed(self):
        self.rpc('CreateTransaction', self.tx())
        res = self.rpc('CancelTransaction', {'id': 'tx-001', 'reason': 3})
        self.assertEqual(res.json()['result']['state'], -1)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'cancelled')

    def test_unknown_transaction_is_not_found(self):
        self.assertEqual(self.rpc('CheckTransaction', {'id': 'nope'}).json()['error']['code'], -31003)
