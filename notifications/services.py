"""
Bildirishnomalar yuborish servislari
"""
import requests
from django.conf import settings
from django.core.mail import send_mail
from .models import Notification, TelegramSubscriber


def send_notification(user, type, title, message, link='', send_email=False, send_telegram=False):
    """
    Universal bildirishnoma yuborish funksiyasi.
    Saytdagi notification + (ixtiyoriy) email + telegram.
    """
    notification = Notification.objects.create(
        user=user,
        type=type,
        title=title,
        message=message,
        link=link,
    )

    if send_email and user.email:
        try:
            send_mail(
                subject=title,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass

    if send_telegram:
        try:
            telegram = TelegramSubscriber.objects.get(user=user, is_active=True)
            send_telegram_message(telegram.chat_id, f"<b>{title}</b>\n\n{message}")
        except TelegramSubscriber.DoesNotExist:
            pass

    return notification


def send_telegram_message(chat_id, text):
    """Telegram bot orqali xabar yuborish"""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return False

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, json={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML',
        }, timeout=10)
        return response.ok
    except Exception:
        return False
