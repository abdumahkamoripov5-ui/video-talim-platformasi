import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Tariff(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Tarif'
        verbose_name_plural = 'Tariflar'
        ordering = ['order']

    def __str__(self):
        return f"{self.name} — {self.price} so'm"


class Payment(models.Model):
    PROVIDER_CHOICES = [
        ('payme', 'Payme'),
        ('click', 'Click'),
        ('uzum', 'Uzum Bank'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('paid', "To'langan"),
        ('failed', 'Rad etildi'),
        ('cancelled', 'Bekor qilindi'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    tariff = models.ForeignKey(Tariff, on_delete=models.SET_NULL, null=True)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    duration_days = models.PositiveIntegerField(default=30)
    external_id = models.CharField(max_length=255, blank=True)
    provider_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} — {self.amount} so'm ({self.get_status_display()})"

    def activate_subscription(self):
        from django.db import transaction
        from django.contrib.auth import get_user_model
        with transaction.atomic():
            payment = Payment.objects.select_for_update().select_related('tariff').get(pk=self.pk)
            if payment.status != 'pending':
                return False
            user = get_user_model().objects.select_for_update().get(pk=payment.user_id)
            now = timezone.now()
            start = max(user.subscription_end, now) if user.subscription_end else now
            user.subscription_start = now
            user.subscription_end = start + timedelta(days=payment.duration_days)
            user.save(update_fields=['subscription_start', 'subscription_end'])
            payment.status = 'paid'
            payment.paid_at = now
            payment.save(update_fields=['status', 'paid_at'])
            self.status, self.paid_at = payment.status, payment.paid_at
            return True
