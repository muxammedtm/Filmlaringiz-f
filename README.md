# 🎬 Mukammal Kino Bot — O'rnatish Qo'llanmasi

> Ushbu versiyada **xavfsizlik tuzatishlari** + ikkita yangi funksiya qo'shildi:
> 1. Kino qo'shilganda kanalga **poster (skrinshot)** + «Kinoni ko'rish» tugmasi chiqadi
>    (tugma botga olib kirib, kinoni avtomatik yuboradi).
> 2. Admin paneldan **Instagram** sahifa va **qo'shimcha Telegram bot** manzilini
>    kiritish mumkin — ular barcha postlarga chiqadi.

---

## ⚠️ MUHIM XAVFSIZLIK (avval shuni o'qing)

1. **Bot tokeni endi kodda saqlanmaydi.** Faqat environment variable orqali beriladi.
   Agar eski tokeningiz GitHub'ga chiqib ketgan bo'lsa — **@BotFather → `/revoke`**
   orqali uni darhol bekor qiling va yangisini oling.
2. **`kinobot.db` ni hech qachon repoga qo'ymang** — unda real foydalanuvchilar bor.
   `.gitignore` allaqachon uni e'tiborsiz qoldiradi.

---

## ⚙️ 1-QADAM: Environment variables

Tokenni va sozlamalarni env orqali bering (koddagi `config.py` ni o'zgartirmaysiz):

```bash
export BOT_TOKEN="1234567890:AAABB..."   # BotFather tokeni
export OWNER_ID="123456789"              # Sizning Telegram ID
export BOT_USERNAME="MyKinoBot"          # ixtiyoriy (admin paneldan ham bo'ladi)
export POST_CHANNEL="-1001234567890"     # ixtiyoriy (admin paneldan ham bo'ladi)
```

**Telegram ID qanday topish?** → [@userinfobot](https://t.me/userinfobot) ga `/start`.

---

## 📦 2-QADAM: Kutubxona o'rnatish

```bash
pip install -r requirements.txt
```

---

## 🚀 3-QADAM: Ishga tushirish

```bash
python main.py
```

Token bo'lmasa bot ishga tushmaydi va aniq xato beradi.

---

## 🎬 Kino Qo'shish (yangilangan)

`/admin` → **🎬 Kinolar** → **➕ Qo'shish**

1. Nom → Tavsif (yoki `/skip`) → Yil → Janr → Kategoriya → **Kod**
2. **Fayl** (video/dokument)
3. **Poster (rasm/skrinshot)** — yangi qadam. `/skip` bilan o'tkazib yuborish mumkin.

Agar **Post kanali** sozlangan bo'lsa, kanalga **poster rasm** + ostida
**«🎬 Kinoni ko'rish»** tugmasi chiqadi. Tugma `https://t.me/bot?start=KOD`
deep-link bo'lib, foydalanuvchini botga kiritadi va o'sha kinoni avtomatik yuboradi.
Poster yuborilmasa — kanalga faqat matnli post chiqadi.

Mavjud kinoga keyin poster qo'shish: **Kino → ✏️ Tahrirlash → 🖼 Poster**.

---

## 📸 Instagram va Qo'shimcha bot (yangi)

`/admin` → **⚙️ Sozlamalar:**
- **📸 Instagram** — username (`kino_uz`) yoki to'liq link.
- **🎬 Qo'shimcha bot** — ikkinchi botning username (`IkkinchiBot`).

Ikkalasi ham kanal postiga va botdagi kino xabariga tugma + matn bo'lib chiqadi.
O'chirish uchun `/clear` yuboring.

---

## 👑 Admin Rollari (endi haqiqatda ishlaydi)

| Rol | Ruxsat |
|-----|--------|
| `super_admin` | Hamma narsa |
| `moderator` | Kinolar + foydalanuvchilar |
| `content_admin` | Faqat kino qo'shish/tahrirlash |
| `ads_admin` | Faqat broadcast |

Admin panelda har bir admin faqat o'z roli ruxsat bergan bo'limlarni ko'radi va
o'sha bo'limlardagina amal bajara oladi (server tomonda tekshiriladi). Egasi
(`OWNER_ID`) doimo hamma narsaga ega.

---

## 🔒 Himoya Tizimi

`/admin` → **⚙️ Sozlamalar:**
- **Forward bloklash** va **Saqlash bloklash** — biri yoqilsa, yuborilgan kinoda
  `protect_content` yoqiladi (Telegram forward va saqlashni bloklaydi).

---

## 📢 Majburiy Kanal

1. Botni kanalga **Admin** qiling.
2. `/admin` → **📢 Kanallar** → **➕ Qo'shish** → username yoki invite link.
3. **🔒 Obuna holati** → YOQISH.

Obuna hisobi endi **bazada doimiy** saqlanadi — bot qayta ishga tushganda
qaytadan sanalmaydi.

---

## 🌐 bothost.ru / Docker da Deploy

Environment Variables:
```
BOT_TOKEN=sizning_tokeningiz
OWNER_ID=sizning_id
BOT_USERNAME=botusername
POST_CHANNEL=-100...
DATA_DIR=/app/data        # Docker volume — baza shu yerda saqlanadi
```
Start file: `main.py`

---

## 🐛 Xato bo'lsa

```bash
tail -f bot.log
```
