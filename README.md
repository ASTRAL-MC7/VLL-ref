# VLL_PREM_BOT — referal bot (Render + Neon)

## 1. Botni yaratish
BotFather orqali bot yaratilgan bo'lsa (username: `@VLL_PREM_BOT`), tokenni saqlab qo'ying.
Botni ikkala kanalga ham **admin** qilib qo'shing (a'zolikni tekshirish uchun shart).

## 2. Neon (Postgres) bazasi
1. https://neon.tech da project yarating.
2. "Connection string" ni nusxalang — bunday ko'rinishda bo'ladi:
   `postgresql://user:password@ep-xxxx.neon.tech/dbname?sslmode=require`
3. Buni keyinroq `DATABASE_URL` env-o'zgaruvchisiga qo'yasiz. Jadvallarni bot
   birinchi ishga tushganda o'zi yaratadi (`database.py` -> `init_pool`).

## 3. Yopiq (private) kanal uchun chat_id olish
Ikkinchi kanal (`https://t.me/+tEUbmGCU-jUxZWYy`) taklif-havola bilan, ya'ni
public username yo'q. Telegram Bot API a'zolikni tekshirish uchun raqamli
`chat_id` (masalan `-1001234567890`) talab qiladi — botlar taklif-havoladan
buni o'zi ololmaydi. Buni bir marta qo'lda olish kerak:

1. Botni shu kanalga admin qilib qo'shing.
2. Kanalda istalgan xabarni (masalan eski postni) **@userinfobot** ga forward
   qiling — u sizga kanalning raqamli ID sini ko'rsatadi (`-100...` bilan
   boshlanadi). Yoki kanalga vaqtincha biror post yozib, uni botga forward
   qilib, `message.forward_from_chat.id` orqali ham olsa bo'ladi.
3. Olingan raqamni `config.py` faylida ikkinchi kanalning `chat_id` maydoniga
   yozing:

```python
{
    "title": "VLL Premium Chat",
    "url": "https://t.me/+tEUbmGCU-jUxZWYy",
    "username": None,
    "chat_id": -1001234567890,   # <-- shu yerga
},
```

Public kanal (`VLLPrem`) uchun hech narsa qilish shart emas — `username`
orqali avtomatik tekshiriladi.

## 4. Render'da deploy qilish
1. Bu papkani GitHub repo qiling va Render'da **New + Web Service** tanlang,
   repo'ni ulang.
2. Sozlamalar:
   - **Runtime**: Python 3
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `python main.py`
3. **Environment** bo'limida quyidagilarni qo'shing:
   | Key | Value |
   |---|---|
   | `BOT_TOKEN` | BotFather bergan token |
   | `DATABASE_URL` | Neon connection string |
   | `ADMIN_IDS` | `5523761749` (vergul bilan bir nechta id qo'yish mumkin) |
   | `BOT_USERNAME` | `VLL_PREM_BOT` |
   | `WEBHOOK_SECRET` | ixtiyoriy, o'zingiz o'ylab topgan maxfiy so'z |

   `RENDER_EXTERNAL_URL` ni Render o'zi avtomatik beradi — webhook shu manzilga
   sozlanadi, qo'lda hech narsa qilish shart emas.
4. Deploy tugagach, bot avtomatik webhook o'rnatadi (loglarda "Webhook set to
   ..." deb chiqadi).

## 5. Foydalanuvchi oqimi
- `/start` — kanallarga qo'shilish tugmalari + "✅ Tekshirish" chiqadi.
- Tekshiruvdan o'tsa: ro'yxatdan o'tadi (+1 Vcoin), agar kimningdir
  referal-havolasi orqali kirgan bo'lsa, o'sha odamga +1 referal va +1 Vcoin
  beriladi.
- Asosiy menyu (hammasi inline tugma):
  - 💰 Mening balim — Vcoin va referal sonini ko'rsatadi
  - 🔗 Mening linkim — admin sozlagan xabar (rasm/matn) + shaxsiy havola
  - 📊 Statistika — TOP 3 va foydalanuvchining o'z o'rni (`#82 - o'rin siz`)
  - 🏆 Sovg'alar — 1/2/3-o'rin sovg'alari

## 6. Admin buyruqlari
- `/admin` — inline panel: Users count, Stats (top 10)
- `/addref <user_id> <amount>` — referal sonini qo'shadi
- `/delref <user_id> <amount>` — referal sonini ayiradi
- `/refmessage` — bot "linkim" tugmasi bosilganda yuboradigan xabarni so'raydi
  (matn, rasm yoki rasm+izoh); har doim oxiriga foydalanuvchining shaxsiy
  havolasi avtomatik qo'shiladi.

## 7. Mahalliy test (ixtiyoriy)
Webhook o'rniga polling bilan sinab ko'rish uchun `main.py`dagi webhook
qismini vaqtincha `dp.start_polling(bot)` bilan almashtirishingiz mumkin —
lekin Render'ga deploy qilganda webhook varianti kerak bo'ladi.
