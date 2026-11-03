from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Foydalanuvchilar'

    def ready(self):
        from django.contrib import admin
        from .admin_dashboard import get_admin_urls

        original_get_urls = admin.site.get_urls

        def get_urls():
            return get_admin_urls() + original_get_urls()

        admin.site.get_urls = get_urls
        admin.site.site_header = "Video Ta'lim Platformasi"
        admin.site.site_title = "Admin Panel"
        admin.site.index_title = "Boshqaruv"
