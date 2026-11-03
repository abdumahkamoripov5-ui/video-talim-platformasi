from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import Category, Course, Lesson
from payments.models import Tariff

User = get_user_model()


class Command(BaseCommand):
    help = "Test ma'lumotlarini yaratadi (kategoriyalar, kurslar, darslar, tariflar)"

    def handle(self, *args, **options):
        # Tariflar
        tariffs_data = [
            {'name': '1 oylik', 'price': 99000, 'duration_days': 30, 'order': 1,
             'description': "Bir oylik to'liq kirish"},
            {'name': '3 oylik', 'price': 270000, 'duration_days': 90, 'order': 2,
             'description': "3 oylik tejamkor tarif (10% chegirma)"},
            {'name': '1 yillik', 'price': 990000, 'duration_days': 365, 'order': 3,
             'description': "Yillik tarif (eng arzon, 17% chegirma)"},
        ]
        for t in tariffs_data:
            Tariff.objects.update_or_create(name=t['name'], defaults=t)
        self.stdout.write(self.style.SUCCESS(f"[OK]{len(tariffs_data)} ta tarif yaratildi"))

        # Kategoriyalar
        categories_data = [
            {'name': 'Dasturlash', 'slug': 'dasturlash', 'icon': '💻'},
            {'name': 'Dizayn', 'slug': 'dizayn', 'icon': '🎨'},
            {'name': 'Marketing', 'slug': 'marketing', 'icon': '📈'},
            {'name': 'Tillar', 'slug': 'tillar', 'icon': '🌐'},
        ]
        cats = {}
        for c in categories_data:
            cat, _ = Category.objects.update_or_create(slug=c['slug'], defaults=c)
            cats[c['slug']] = cat
        self.stdout.write(self.style.SUCCESS(f"[OK]{len(categories_data)} ta kategoriya yaratildi"))

        # Kurslar
        courses_data = [
            {
                'title': 'Python Asoslari',
                'slug': 'python-asoslari',
                'description': "Python dasturlash tilini noldan boshlab o'rganamiz. O'zgaruvchilar, sikllar, funksiyalar va OOP.",
                'instructor': 'Akbar Rashidov',
                'category': cats['dasturlash'],
                'is_published': True,
                'order': 1,
            },
            {
                'title': 'JavaScript va React',
                'slug': 'javascript-react',
                'description': "Zamonaviy frontend dasturlash. JavaScript ES6+ va React kutubxonasi.",
                'instructor': 'Sevara Karimova',
                'category': cats['dasturlash'],
                'is_published': True,
                'order': 2,
            },
            {
                'title': 'Figma bilan UI/UX',
                'slug': 'figma-ui-ux',
                'description': "Figma'da professional dizayn yaratish. Wireframe, prototype, design system.",
                'instructor': 'Dilshod Yusupov',
                'category': cats['dizayn'],
                'is_published': True,
                'order': 3,
            },
            {
                'title': 'SMM va Reklama',
                'slug': 'smm-reklama',
                'description': "Ijtimoiy tarmoqlarda marketing strategiyasi va targetlangan reklama.",
                'instructor': 'Malika Tursunova',
                'category': cats['marketing'],
                'is_published': True,
                'order': 4,
            },
        ]

        for c in courses_data:
            course, _ = Course.objects.update_or_create(slug=c['slug'], defaults=c)

            # Har bir kurs uchun 5 ta dars
            for i in range(1, 6):
                Lesson.objects.update_or_create(
                    course=course,
                    order=i,
                    defaults={
                        'title': f"{i}-dars: {c['title']} — {i}-bo'lim",
                        'description': f"Bu darsda {c['title'].lower()} mavzusining {i}-qismini o'rganamiz.",
                        'is_published': True,
                        'is_free_preview': (i == 1),  # Birinchi dars bepul preview
                        'duration_seconds': 600 + i * 120,
                    },
                )
        self.stdout.write(self.style.SUCCESS(f"[OK]{len(courses_data)} ta kurs (har birida 5 dars) yaratildi"))

        self.stdout.write(self.style.SUCCESS("\n[OK] Test ma'lumotlari muvaffaqiyatli qo'shildi!"))
        self.stdout.write(self.style.WARNING("\nEslatma: Kurs va dars rasmlari yo'q — admin paneldan qo'lda yuklang."))
