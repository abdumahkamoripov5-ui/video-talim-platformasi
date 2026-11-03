# EduPlatform — Video Ta’lim Platformasi

React + Django asosidagi obunali ta’lim platformasi. Veb sayt Vercelga,
backend esa PostgreSQL, Redis/Celery, FFmpeg va doimiy fayl diskiga ega serverga joylanadi.

## Ishga tushirish

Python 3.12 va Node.js 22.13+ kerak. Mavjud `.env` bo‘lsa, ustiga yozmang;
yangi o‘rnatishda `.env.example` asosida `.env` yarating va SECRET_KEY kiriting.

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Alohida terminalda:

```bash
cd frontend
npm ci
npm run dev
```

Veb: http://localhost:5173. Admin: http://localhost:8000/admin/.
Dashboard: http://localhost:8000/admin/dashboard/. API: http://localhost:8000/api/docs/.
Namuna kurslari uchun ixtiyoriy `python manage.py seed_data` buyrug‘i mavjud;
u haqiqiy videolar yoki admin akkaunt yaratmaydi.

## Asosiy imkoniyatlar

- Kurs katalogi, kategoriya/qidiruv/reyting/saralash va sahifalash.
- Login/ro‘yxatdan o‘tish paytida serverda tekshiriladigan ikki qurilma limiti.
- Qurilma o‘chirilganda access va refresh tokenlari bekor bo‘ladi.
- 360p/720p/1080p HLS, avtomatik sifat tanlash, resume playback va progress.
- Qurilmaga bog‘langan, muddati cheklangan video playlist/segment endpointlari.
- Obuna bilan himoyalangan PDF/Word materiallar va autentifikatsiyali sertifikat yuklash.
- To‘lov callbacklarida autentifikatsiya, summa tekshiruvi va takroriy aktivatsiyadan himoya.
- Admin orqali video yuklash, Celery workerda konvertatsiya, IP/qurilma/progress monitoringi.
- Desktop/mobil dizayn, och/qorong‘i mavzu, navigatsiyada UZ/RU/EN; barcha matnlarning tarjimasi hali to‘liq emas.

Default obuna 30 kun, admin tarifning davomiyligini sozlay oladi. Obuna muddati
har bir to‘lovda saqlanadi; keyingi tarif o‘zgarishi yaratilgan buyurtmaga ta’sir qilmaydi.
Faol obuna ustiga qayta to‘lov qolgan muddatga qo‘shiladi. Muddati tugaganda kirish yopiladi.

## Tekshirish

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test tests
cd frontend
npm run lint
npm run build
```

FFmpeg integratsiya testi haqiqiy videoni uchta HLS sifatiga aylantirib ffprobe bilan tekshiradi.
FFmpeg tizimda o‘rnatilmagan bo‘lsa, faqat shu test o‘tkazib yuboriladi.

## Internetga chiqarish

GitHub va Vercel bo‘yicha to‘liq yo‘riqnoma: [DEPLOYMENT.md](DEPLOYMENT.md).
Vercel konfiguratsiyasi `frontend/vercel.json` da. Production backend uchun
`Dockerfile`, `compose.yaml` va `deploy/production.env.example` mavjud.

Productionda `CELERY_TASK_ALWAYS_EAGER=False` va Celery worker kerak.
Developmentda `True` video konvertatsiyasini shu jarayonda bajaradi.
Asl videolar va dars materiallari ochiq `/media` manzilidan tarqatilmaydi.

## Alohida yakunlanadigan ishlar

- Payme/Click/Uzum merchant shartnomalari, haqiqiy kalitlar va provider sandbox sertifikatsiyasi.
  Kalitlar yo‘q bo‘lsa, checkout 503 va tushunarli xabar qaytaradi.
- CDN edge avtorizatsiyasi, real serverlarda yuklama sinovi, monitoring va backup.
  Docker konfiguratsiyasi o‘zi yuqori yuklamaga kafolat bermaydi.
- Native Android/iOS ilovalar, ekran yozish himoyasi va store nashri.
  Responsive veb/PWA native ilova o‘rnini to‘liq bosmaydi.
- Brauzerdagi watermark/nodownload mutlaq DRM emas va o‘chirib bo‘lmasligi kafolatlanmaydi.
  Sekin tarmoqda HLS ham buffering qilishi mumkin.
- To‘langan obunani qaytarish avtomatlashtirilmagan; provider bekor qilish so‘rovi xavfsiz rad etilib,
  qaytarish alohida tekshiriladi. Veb ekran yozishni to‘liq bloklay olmaydi.

Maxfiy `.env`, bazalar, media va virtual muhitni GitHubga yubormang.
