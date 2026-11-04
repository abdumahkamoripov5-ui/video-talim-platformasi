# Vercel: frontend va Django API

Bu rejim login, ro‘yxatdan o‘tish, kurslar, testlar, progress va admin panelni
ishga tushirish uchun. PostgreSQL tashqi xizmatda turadi. Fayllar, video yuklash,
HLS va FFmpeg worker hali ulanmagan: faylli so‘rovlar 503 bilan aniq xabar qaytaradi.
Faylsiz kurs va darslarni boshqarish mumkin (majburiy thumbnail talab qiladigan
kurs yaratish uchun keyinchalik doimiy fayl saqlashni ulash kerak).
Video worker va private storage ulanishi alohida bosqich; vaqtinchalik diskdagi
videolarni production yechim deb hisoblamang. To‘lov merchant kalitlari ham alohida.

## 1. PostgreSQL yaratish

Neon (https://console.neon.tech/) hisobiga GitHub orqali kiring.
Yangi loyiha va PostgreSQL bazasi yarating. Connect oynasidan pooler yoqilgan
PostgreSQL connection stringni oling. U `postgresql://` bilan boshlanadi.
Bu qiymat maxfiy: chatga yoki GitHubga yubormang.
Bepul tarif limiti va shartlarini hisob ochish paytida tekshiring.

## 2. Vercel loyihasini sozlash

Mavjud `video-talim-platformasi` loyihasi -> Settings -> Build and Deployment:
Root Directory ni `frontend` dan loyiha ildiziga (`./`) o‘zgartiring.
Frontend-only build/output/install override sozlamalarini o‘chiring; ildizdagi
`vercel.json` har bir xizmatni alohida sozlaydi. Services aniqlansa shu rejimni tanlang.
Frontend uchun Node.js 22.x ishlating.

Xizmatlar: `backend` (Django, ildiz papka) va `frontend` (Vite, frontend papka).
`/api/*`, `/admin/*`, `/static/*`, `/media/*` backendga; qolgan yo‘llar frontendga boradi.
Frontend SPA ichidagi sahifalarni o‘zining `frontend/vercel.json` fayli boshqaradi.
Brauzer `/api` orqali murojaat qiladi. Serverdan boshqa xizmatga ichki so‘rov yo‘q,
shuning uchun service binding qo‘shilmagan. `/media` hozir fayl saqlashni ta’minlamaydi.

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
