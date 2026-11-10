from unittest.mock import patch
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

SECRET = 'bot-secret-123'


@override_settings(TELEGRAM_BOT_TOKEN='123:TEST', TELEGRAM_WEBHOOK_SECRET=SECRET, TELEGRAM_WEBAPP_URL='https://site.example')
class TelegramStartTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def post(self, update, secret=SECRET):
        headers = {'HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN': secret} if secret else {}
        return self.client.post('/api/notifications/telegram/webhook/', update, format='json', **headers)

    def start(self, chat_type='private'):
        return {'update_id': 1, 'message': {'text': '/start', 'chat': {'id': 555, 'type': chat_type}}}

    def test_rejects_missing_or_wrong_secret(self):
        with patch('notifications.views._send_telegram') as send:
            self.assertEqual(self.post(self.start(), secret=None).status_code, 403)
            self.assertEqual(self.post(self.start(), secret='wrong').status_code, 403)
            send.assert_not_called()

    def test_start_sends_description_and_web_app_buttons(self):
        with patch('notifications.views._send_telegram', return_value=True) as send:
            self.assertEqual(self.post(self.start()).status_code, 200)
        method, payload = send.call_args.args
        self.assertEqual(method, 'sendMessage')
        self.assertEqual(payload['chat_id'], 555)
        self.assertIn('Video Ta', payload['text'])
        buttons = [b for row in payload['reply_markup']['inline_keyboard'] for b in row]
        urls = {b['text']: b['web_app']['url'] for b in buttons}
        self.assertEqual(urls["Ro'yxatdan o'tish"], 'https://site.example/register')
        self.assertEqual(urls['Kirish'], 'https://site.example/login')
        self.assertEqual(urls['Ilovani ochish'], 'https://site.example/')

    def test_start_in_group_is_ignored(self):
        with patch('notifications.views._send_telegram') as send:
            self.post(self.start(chat_type='group'))
            send.assert_not_called()

    def test_other_messages_are_ignored(self):
        with patch('notifications.views._send_telegram') as send:
            self.post({'message': {'text': 'salom', 'chat': {'id': 555, 'type': 'private'}}})
            send.assert_not_called()
