from django.contrib import admin
from django.utils.html import format_html
from .models import Tariff, Payment


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'is_active', 'order')
    list_editable = ('is_active', 'order', 'price')
    ordering = ('order',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'tariff', 'provider', 'amount', 'status_badge', 'created_at', 'paid_at')
    list_filter = ('status', 'provider', 'created_at')
    search_fields = ('user__email', 'external_id')
    readonly_fields = ('id', 'created_at', 'paid_at', 'provider_data')
    actions = ['mark_as_paid']

    def status_badge(self, obj):
        colors = {'paid': 'green', 'pending': 'orange', 'failed': 'red', 'cancelled': 'gray'}
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color:{};font-weight:bold">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Holat'

    def mark_as_paid(self, request, queryset):
        for payment in queryset.filter(status='pending'):
            payment.activate_subscription()
        self.message_user(request, "Tanlangan to'lovlar tasdiqlandi")
    mark_as_paid.short_description = "To'langan deb belgilash"
