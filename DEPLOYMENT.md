# GitHub → Vercel: qadam-baqadam

Bu repozitoriy ikki qismdan iborat: `frontend/` — Vercel uchun React sayt;
Django, PostgreSQL, Redis, Celery va FFmpeg esa doimiy diskka ega backend serverda ishlaydi.
Faqat Vercel deploy qilish login, to‘lov va videolarni ishga tushirmaydi.

## 1. GitHub repozitoriyni aniqlash

Loyiha ildizida `git remote -v` bajaring. Natija bo‘sh bo‘lsa, repo ulanmagan.
GitHub → profilingiz → Repositories bo‘limidan shu loyihani toping va uning URL manzilini oling.
Mavjud boshqa loyiha ustiga yozmang. Bu yerda repo aniqlanmaguncha remote yoki push bajarilmagan.

Agar loyiha yangi bo‘lsa, GitHub → New repository → `video-talim-platformasi` →
Private → Create repository; README va .gitignore qo‘shmang, ular lokalda mavjud.

## 2. Lokal tekshirish va commit

Node.js 22.13+ va Python 3.12 kerak. Terminalda:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py test tests
cd frontend
npm ci
npm run lint
npm run build
cd ..
```

`git status` ni tekshiring: `.env`, `db.sqlite3`, videolar, `node_modules` va `venv`
commitga kirmasligi kerak. Oldin kuzatuvga olingan maxfiy faylni `.gitignore` o‘zi olib tashlamaydi.
Repo tarixida `.env` bo‘lgan bo‘lsa, undagi kalitlarni productionda qayta ishlatmang;
yangi SECRET_KEY va merchant kalitlaridan foydalaning.

```bash
git add .
git commit -m "Improve learning platform and prepare Vercel deployment"
```

**Bu lokal repo tarixida `.env` va `db.sqlite3` bo‘lgan. Yangi GitHub repoga ushbu tarixni
bevosita push qilmang.** Commitdan keyin `python scripts/export_source.py` bajaring.
`release-source.zip` ni boshqa yangi papkaga oching, o‘sha papkada `git init -b main`,
`git add .` va `git commit -m "Initial clean source"` bajaring. Shunda eski maxfiy
fayllar va bazaning Git tarixi yangi repoga o‘tmaydi; asl lokal tarix o‘z joyida qoladi.

Mavjud GitHub repo topilsa, avval uning tarkibi tekshiriladi; tekshirilmagan repoga yangi
tarixni yoki `--force` push yubormang.

Repo manzili tasdiqlanib, toza tarixli papkaga o‘tgach (YOUR_USERNAME/YOUR_REPO ni almashtiring):

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

Remote allaqachon mavjud bo‘lsa, qayta qo‘shmang. Mavjud repo tarixiga push rad etilsa,
`--force` ishlatmang: avval remote tarixini tekshirib birlashtirish kerak.

## 3. Backend server

Ubuntu serverga Docker Engine va Compose o‘rnating. `api.example.uz` domenining
A yozuvini server IP manziliga yo‘naltiring. 80 va 443 portlar ochiq bo‘lsin.
Serverga repo kodini oling va `deploy/production.env.example` asosida `.env` yarating.
SECRET_KEY va PostgreSQL parolini kuchli yangi qiymatlarga almashtiring.
`API_DOMAIN`, `ALLOWED_HOSTS`, `FRONTEND_URL` va `CORS_ALLOWED_ORIGINS` ni o‘zingiznikiga moslang.

```bash
docker compose up -d --build
docker compose exec api python manage.py createsuperuser
docker compose logs --tail=100 api worker gateway
```

Caddy domen uchun HTTPS sertifikat oladi. `https://api.example.uz/api/courses/`
JSON qaytarishi kerak. Admin: `https://api.example.uz/admin/`.
Video yuklanganda Celery worker uni 360p/720p/1080p HLSga aylantiradi.
`media` va `postgres_data` volumelarini muntazam zaxiralang. Deployda `down -v` ishlatmang.

## 4. Vercel uchun backendni bog‘lash

Mahalliy loyihada haqiqiy backend domeningizni yozing:

```bash
cd frontend
npm run configure:vercel -- https://api.example.uz
cd ..
git add frontend/vercel.json
git commit -m "Connect Vercel frontend to backend"
git push
```

Bu `/api/*` va `/media/*` so‘rovlarini backendga uzatuvchi external rewrites yaratadi.
Frontendda `VITE_API_URL=/api` qoldiring: Safari HLS uchun HttpOnly qurilma cookie-si
saytning o‘z originida ishlashi kerak. Vercel orqali yirik video yuklamang;
kontentni backendning o‘z admin panelidan yuklang.

Backend hali mavjud bo‘lmasa, keyingi qadam dizayn previewini chiqaradi;
kurslar/login/video ishlashi uchun 3–4-qadamlarni tugatish kerak.

## 5. Vercel deploy

1. https://vercel.com/new → GitHub bilan kiring.
2. Kerakli GitHub repozitoriyni Import qiling; ko‘rinmasa GitHub ruxsatlarini sozlang.
3. Framework Preset: **Vite**.
4. Root Directory: **frontend**.
5. Build Command: **npm run build**.
6. Output Directory: **dist**.
7. Install Command: **npm ci**.
8. Node.js Version: **22.x**.
9. Environment Variables: **VITE_API_URL=/api**.
10. **Deploy** tugmasini bosing.

Deploydan keyin berilgan `https://....vercel.app` manzilini backenddagi
`FRONTEND_URL` va `CORS_ALLOWED_ORIGINS` ga yozib `docker compose up -d` bajaring.
Keyingi GitHub pushlar Vercelda avtomatik qayta deploy bo‘ladi.

## 6. Ishlayotganini tekshirish

- Bosh sahifa, kurs katalogi va to‘g‘ridan-to‘g‘ri `/courses/...` havolasini ochish.
- Ro‘yxatdan o‘tish, kirish, chiqish, ikki qurilma limiti.
- Admin orqali kurs, dars, thumbnail va PDF/Word material yuklash.
- Video `ready` bo‘lgach tomosha qilish va qayta ochganda davom etish.
- `/media/videos/...` ochiq havolalari 404 qaytarishini tekshirish.
- Merchant test muhitida to‘lov va takroriy callbacklarni tekshirish.

Merchant shartnomalari/kalitlari va Payme/Click/Uzum sandbox sertifikatsiyasi alohida kerak.
CDN/katta yuklama va native Android/iOS ilovalar ushbu Vercel deploy bilan avtomatik yaratilmaydi.
Veb watermark va `nodownload` brauzerda mutlaq DRM emas; uni o‘chirib bo‘lmasligi kafolatlanmaydi.

Manbalar:
- https://vercel.com/docs/frameworks/frontend/vite
- https://vercel.com/docs/monorepos
- https://vercel.com/docs/routing/rewrites
