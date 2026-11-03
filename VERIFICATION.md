# Tekshiruv natijalari — 2026-11-03

- Django system check: xatosiz.
- Migration drift: `makemigrations --check --dry-run` — o‘zgarish yo‘q.
- `python manage.py test tests`: 41 ta test o‘tdi, jumladan haqiqiy FFmpeg konvertatsiyasi.
- Frontend Node 22 bilan `npm ci`, ESLint va Vite production build bajarildi.
- Chromium brauzerda 1440px desktop va 390px mobil ekran tekshirildi.
- Kurs/kategoriya navigatsiyasi, himoyalangan darsdan loginga o‘tish, noto‘g‘ri login holatidan
  tiklanish, ro‘yxatdan o‘tish, kursga yozilish, izoh yozish, profil, chiqish,
  mobil menyu va 404 sahifa tekshirildi. JS page error aniqlanmadi.
- Mobil hero grid kengligi va logoutdan keyingi bekor qilingan token bilan so‘rov yuborish holati tuzatildi.

Brauzer tekshiruvlari vaqtinchalik `/tmp/edu-preview.sqlite3` bazasida bajarildi;
asosiy `db.sqlite3` ga test akkauntlari yozilmadi.

## Hali tasdiqlanmagan talablar

- Haqiqiy Payme/Click/Uzum merchant muhitlari va ularning sandbox sertifikatsiyasi.
- CDN, real yuqori yuklama, production Docker/TLS va zaxira tiklash sinovi.
- Native Android/iOS ilova, ekran yozish himoyasi va app store nashri.
- Veb watermark mutlaq DRM emas; brauzer orqali yozib olishni to‘liq cheklab bo‘lmaydi.
- npm auditda 6 ta moderate ogohlantirish ESLint/minimatch development zanjirida qolgan;
  mos bo‘lmagan major versiyalarni majburan o‘rnatish bajarilmadi. Production dependency va
  development dependency holatlarini deploydan oldin yana tekshiring.

Bu natijalar tekshirilgan oqimlarga tegishli; “hech qanday bug yo‘q” kafolati emas.
