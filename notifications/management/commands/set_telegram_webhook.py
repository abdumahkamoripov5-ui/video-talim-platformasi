import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Telegram botining webhook manzilini sozlaydi (TELEGRAM_BOT_TOKEN va TELEGRAM_WEBHOOK_SECRET kerak)."

    def add_arguments(self, parser):
        parser.add_argument('base_url', help="Sayt manzili, masalan https://video-talim-platformasi.vercel.app")

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_WEBHOOK_SECRET:
            raise CommandError('TELEGRAM_BOT_TOKEN va TELEGRAM_WEBHOOK_SECRET sozlanmagan')
        url = options['base_url'].rstrip('/') + '/api/notifications/telegram/webhook/'
        response = requests.post(
            f'https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook',
            json={'url': url, 'secret_token': settings.TELEGRAM_WEBHOOK_SECRET, 'allowed_updates': ['message']},
            timeout=20,
        )
        self.stdout.write(f'{response.status_code} {response.text}')
