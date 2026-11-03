from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('payment', "To'lov"),
        ('subscription', 'Obuna'),
        ('answer', 'Javob'),
        ('certificate', 'Sertifikat'),
        ('course', 'Yangi kurs'),
        ('system', 'Tizim'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bildirishnoma"
        verbose_name_plural = "Bildirishnomalar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email}: {self.title}"


class TelegramSubscriber(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='telegram')
    chat_id = models.CharField(max_length=50, unique=True)
    username = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Telegram obunachi"
        verbose_name_plural = "Telegram obunachilar"

    def __str__(self):
        return f"{self.user.email} → @{self.username or self.chat_id}"
