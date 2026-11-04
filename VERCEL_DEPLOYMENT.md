# Vercel: bitta Django loyiha va React frontend

Bu rejim login, ro‘yxatdan o‘tish, kurslar, testlar, progress va admin panelni
ishga tushiradi. PostgreSQL tashqi xizmatda turadi. Video, rasm va dars materiallarini
Neon Object Storage ga ulash: [OBJECT_STORAGE.md](OBJECT_STORAGE.md).
MP4 videolar konvertatsiyasiz ishlaydi. HLS/FFmpeg uchun alohida worker kerak.
To‘lov merchant kalitlari ham alohida sozlanadi.

## 1. PostgreSQL yaratish

Neon (https://console.neon.tech/) hisobiga GitHub orqali kiring.
Yangi loyiha va PostgreSQL bazasi yarating. Connect oynasidan pooler yoqilgan
PostgreSQL connection stringni oling. U `postgresql://` bilan boshlanadi.
Bu qiymat maxfiy: chatga yoki GitHubga yubormang.
Bepul tarif limiti va shartlarini hisob ochish paytida tekshiring.

## 2. Vercel loyihasini sozlash

Mavjud `video-talim-platformasi` loyihasi -> Settings -> Build and Deployment:
Root Directory ni loyiha ildiziga (`./`) qo‘ying.
Framework Preset: **Django**. Oldingi frontend-only install/output override
sozlamalarini o‘chiring. Build Command `python scripts/vercel_build.py`.
Node.js Version **22.x**. Frontend `npm ci` va Vite orqali build vaqtida yig‘iladi,
keyin Django collectstatic orqali `/static/` dan tarqatiladi. Django React
sahifalarini ham beradi; API `/api/`, admin `/admin/` da ishlaydi.
Services va ichki bindings ishlatilmaydi. `/api/health/` JSON qaytarishi kerak.

## 3. Environment Variables

Settings -> Environment Variables: `deploy/vercel.env.example` dagi nomlarni
**Production** uchun kiriting. `DATABASE_URL` ga Neon bergan haqiqiy URLni yozing.
`SECRET_KEY` uchun yangi uzun tasodifiy qiymat yarating, masalan lokal terminalda:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

`ALLOWED_HOSTS` ga protokolsiz domen, `FRONTEND_URL` va `CORS_ALLOWED_ORIGINS` ga
`https://` bilan to‘liq domen yoziladi. Yangi domen bo‘lsa qiymatlarni moslang.
`RUN_MIGRATIONS=true` production buildda bazadagi jadvallarni yaratadi/yangilaydi.
Build tugamaguncha migration xatosi bo‘lsa deploy to‘xtaydi. Destruktiv migrationdan
oldin bazani zaxiralang. Preview uchun alohida Neon branch/baza ishlating;
production DATABASE_URL va RUN_MIGRATIONS ni Preview ga qo‘ymang.
Vercel bergan VERCEL_* o‘zgaruvchilarini qo‘lda kiritmang.

## 4. Deploy va tekshirish

Deployments -> eng so‘nggi commit -> Redeploy. Zarur bo‘lsa build cache ni o‘chiring.
Build logda backend va frontend muvaffaqiyatli yig‘ilganini tekshiring.

- `/api/health/` -> `{"status":"ok"}`.
- `/api/courses/` -> JSON, HTML yoki Vercel 404 emas.
- `/register` orqali hisob oching, `/login` orqali kiring.
- Sahifani yangilab frontend routingni tekshiring.
- `/admin/login/` Django admin login sahifasini ochishi kerak.

Oddiy foydalanuvchi ro‘yxatdan o‘tganda admin bo‘lmaydi. Admin yaratish uchun lokal
Python 3.12 muhitida production bazaga ulanib quyidagini bajaring. Maxfiy qiymatlarni
terminal tarixiga yozmasdan, vaqtinchalik lokal `.env` orqali kiriting; mavjud lokal
`.env` ni avval xavfsiz saqlang, ustiga yozmang.

```bash
pip install -r requirements.txt
python manage.py createsuperuser
```

Lokal buyruq uchun `.env` dagi DATABASE_URL production bazanikiga mos bo‘lishi kerak.
Ish tugagach lokal konfiguratsiyani qaytaring. Admin parolini Vercel env ga saqlamang.

## Manbalar

- https://vercel.com/docs/services
- https://vercel.com/docs/services/routing
- https://vercel.com/docs/frameworks/full-stack/django
- https://neon.com/docs/connect/connect-from-any-app
