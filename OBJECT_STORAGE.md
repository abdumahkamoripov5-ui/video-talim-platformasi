# Video va materiallar: Neon Object Storage

Admin: `/admin/media-upload/`. Faqat admin sessiyasi va tegishli model ruxsatlari
bilan ishlaydi. Bucket private bo‘ladi; brauzerga yozish kalitlari yuborilmaydi.
Katta fayl Vercel orqali o‘tmay, imzolangan PUT URL orqali bevosita Neon ga boradi.
Yuklashdan so‘ng Django hajm va turini tekshiradi, rasmni Pillow bilan tekshiradi,
faylni brauzer yoza olmaydigan final key ga ko‘chiradi va darsga bog‘laydi.
Yuklashni tasdiqlash takrorlansa yangi material yaratilmaydi.

## 1. Bucket yaratish

Neon -> video-talim-platformasi -> production -> Object storage -> New bucket.
Nom: `edu-media`. Access: **Private**. Public/public_read ni tanlamang.
Neon Free tarifida hozir 5 GB Object Storage mavjud; trafik va boshqa
limitlarni hisobingizdagi Usage sahifasidan kuzating. Bu cheksiz video hosting emas.

## 2. Server kalitlarini olish

Neon Connect -> Storage yoki Object storage ulanish oynasini oching.
Branch **production** uchun `storage:read` va `storage:write` ruxsatli credential oling.
Database paroli yoki Postgres connection string bu yerda ishlamaydi.
Quyidagi qiymatlarni faqat Vercel -> Settings -> Environment Variables -> Production ga yozing:

| Key | Type | Value |
| --- | --- | --- |
| `AWS_ENDPOINT_URL_S3` | Config | Neon bergan to‘liq HTTPS storage endpoint |
| `AWS_ACCESS_KEY_ID` | Secret | Storage access key ID |
| `AWS_SECRET_ACCESS_KEY` | Secret | Storage secret access key |
| `AWS_REGION` | Config | Ohio uchun `us-east-2` |
| `MEDIA_BUCKET` | Config | `edu-media` |
| `OBJECT_STORAGE_ENABLED` | Config | `True` (boshqa qiymatlardan keyin) |

Kalitlarga VITE_ prefiksini qo‘ymang, chatga yoki GitHubga yubormang.
`FRONTEND_URL` haqiqiy production domeni bo‘lishi kerak. So‘ng yangi commitni redeploy qiling.

## 3. Brauzer yuklash ruxsatini sozlash

Superuser bilan `/admin/` ga kiring, “Video, dars materiali yoki kurs rasmini yuklash”
havolasini oching. **Saqlash ulanishini tekshirish va sozlash** tugmasini bosing.
Bu mavjud bucketni tekshiradi va faqat FRONTEND_URL domeniga GET, HEAD, PUT uchun
CORS qoidasini o‘rnatadi. Avvalgi bucket CORS qoidalari shu qoida bilan almashtiriladi;
shuning uchun bu loyiha uchun alohida bucket ishlating. Bucket yaratish va private access
Neon panelida bajariladi. Oddiy admin CORS ni o‘zgartira olmaydi.

## 4. Kurs, dars va fayl yuklash

1. Admin panelda kurs yarating. Kurs rasmini dastlab bo‘sh qoldirish mumkin.
2. Dars yarating. Sinov uchun bepul ko‘rish va publish belgilari yoqilgan bo‘lsin.
3. `/admin/media-upload/` da turini va kurs/darsni tanlang.
4. Fayl tanlang -> Yuklash. “Tayyor” chiqmaguncha sahifani yopmang.
5. Saytda darsni ochib ko‘ring, materialni yuklab oling, sahifani yangilab tekshiring.

MP4: brauzerda ijro qilinadigan H.264/AAC format, 1 GB gacha.
PDF, DOC, DOCX, TXT, ZIP: 100 MB gacha. JPG, PNG, WebP: 2 MB gacha.
Limitlar DIRECT_VIDEO_MAX_BYTES va DIRECT_ATTACHMENT_MAX_BYTES bilan o‘zgartiriladi.
Katta videoni internet uzilganda boshidan yuklash kerak; multipart/resumable upload bu
versiyaga kirmaydi. 360p/720p/1080p avtomatik yaratilmaydi; HLS pipeline alohida workerda qoladi.

Adminning oddiy file-inputlari Vercelda bloklangan: har doim maxsus yuklash sahifasidan
foydalaning. Bu versiya kurs rasmi, dars videosi va dars materiallarini yuklaydi;
avatar va dars thumbnailini maxsus yuklash sahifasi hozircha qamramaydi.
Video va materialga URL olishdan oldin login, aktiv qurilma va obuna/bepul dars ruxsati
tekshiriladi. MP4 va material havolalari bearer URL: muddati tugaguncha nusxalangan
havola ishlashi mumkin. Bu DRM emas. Video player URLni muddati tugashidan oldin yangilaydi.

## Saqlashni boshqarish

Yangi video yoki rasm avvalgisini almashtiradi, lekin eski object avtomatik o‘chirilmaydi.
Bu avvalgi URLlar yoki zaxiralarni buzmaslik uchun. Keraksiz eski objectlarni faqat
bog‘liqligini tekshirgandan keyin Neon panelidan o‘chiring. Muvaffaqiyatli yuklashning
staging objecti o‘chiriladi; tashlab ketilgan yuklashlarni va `uploads/pending/` ostidagi
2 soatdan eski objectlarni vaqt-vaqti bilan tekshiring. Neon lifecycle qoidalari hozir
saqlanadi, lekin avtomatik ijro etilmaydi; avtomatik tozalashga tayanmang.

Kalitlar kiritilmaguncha OBJECT_STORAGE_ENABLED=False qolsin: login/kurslar ishlashda
davom etadi, yuklash sahifasi esa xizmat ulanmaganini ko‘rsatadi.

Manbalar:
- https://neon.com/docs/storage/get-started
- https://neon.com/docs/storage/authentication
- https://neon.com/docs/storage/s3-compatibility
- https://neon.com/docs/storage/buckets
- https://neon.com/docs/introduction/plans
