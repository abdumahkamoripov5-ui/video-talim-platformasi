from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserDevice, VideoProgress


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'phone', 'subscription_status', 'subscription_end', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'full_name', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'display_id')

    fieldsets = (
        ('Asosiy', {'fields': ('id', 'display_id', 'email', 'password')}),
        ("Shaxsiy ma'lumot", {'fields': ('full_name', 'phone', 'avatar')}),
        ('Obuna', {'fields': ('subscription_start', 'subscription_end')}),
        ('Ruxsatlar', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Vaqt', {'fields': ('created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2'),
        }),
    )

    def subscription_status(self, obj):
        if obj.has_active_subscription:
            return format_html('<span style="color:green">✔ Faol</span>')
        return format_html('<span style="color:red">✘ Faol emas</span>')
    subscription_status.short_description = 'Obuna holati'


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_name', 'ip_address', 'last_seen', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'device_id', 'ip_address')
    readonly_fields = ('last_seen', 'created_at')
    actions = ['remove_selected_devices']

    def remove_selected_devices(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} ta qurilma o'chirildi")
    remove_selected_devices.short_description = "Tanlangan qurilmalarni o'chirish"


@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'watched_seconds', 'is_completed', 'updated_at')
    list_filter = ('is_completed',)
    search_fields = ('user__email', 'lesson__title')
