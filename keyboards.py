from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# ─── TIL TANLASH ─────────────────────────────────────────────────────────────

def lang_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        ]
    ])

# ─── ASOSIY MENYU ────────────────────────────────────────────────────────────

def main_menu(lang="uz"):
    if lang == "ru":
        buttons = [
            [KeyboardButton("🎬 Поиск фильма"),   KeyboardButton("⭐ Избранное")],
            [KeyboardButton("🔥 ТОП фильмов"),    KeyboardButton("🆕 Новые")],
            [KeyboardButton("🔀 Случайный"),       KeyboardButton("📜 История")],
            [KeyboardButton("🌐 Язык"),            KeyboardButton("ℹ️ Помощь")],
        ]
    else:
        buttons = [
            [KeyboardButton("🎬 Kino qidirish"),  KeyboardButton("⭐ Sevimlilar")],
            [KeyboardButton("🔥 TOP kinolar"),     KeyboardButton("🆕 Yangi kinolar")],
            [KeyboardButton("🔀 Tasodifiy kino"),  KeyboardButton("📜 Tarix")],
            [KeyboardButton("🌐 Til"),             KeyboardButton("ℹ️ Yordam")],
        ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# ─── OBUNA ───────────────────────────────────────────────────────────────────

def subscription_keyboard(channels: list, lang="uz"):
    rows = []
    for ch in channels:
        if ch.get("invite_link") and ch["invite_link"].startswith("https://"):
            url = ch["invite_link"]
        elif ch.get("username", "").startswith("@"):
            url = f"https://t.me/{ch['username'].lstrip('@')}"
        else:
            url = ch.get("username", "")
        rows.append([InlineKeyboardButton(f"📢 {ch['title']}", url=url)])
    label = "✅ Tekshirish" if lang == "uz" else "✅ Проверить"
    rows.append([InlineKeyboardButton(label, callback_data="check_sub")])
    return InlineKeyboardMarkup(rows)

# ─── PROMO TUGMALAR (Instagram / qo'shimcha bot) ─────────────────────────────

def _promo_rows(bot_username="", channel_username="", instagram="", extra_bot=""):
    """Kino postlari va kanal postlari uchun umumiy promo tugmalar."""
    rows = []
    if bot_username:
        rows.append([InlineKeyboardButton("🤖 Botga o'tish", url=f"https://t.me/{bot_username}")])
    if channel_username:
        rows.append([InlineKeyboardButton("📢 Kanalga o'tish", url=f"https://t.me/{channel_username}")])
    if extra_bot:
        rows.append([InlineKeyboardButton("🎬 Yana bir bot", url=f"https://t.me/{extra_bot}")])
    if instagram:
        rows.append([InlineKeyboardButton("📸 Instagram", url=_insta_url(instagram))])
    return rows


def _insta_url(instagram: str) -> str:
    instagram = instagram.strip()
    if instagram.startswith("http://") or instagram.startswith("https://"):
        return instagram
    return f"https://instagram.com/{instagram.lstrip('@')}"

# ─── KINO TUGMALARI (foydalanuvchiga) ────────────────────────────────────────

def movie_keyboard(movie_id, is_fav=False, lang="uz",
                   bot_username="", channel_username="", instagram="", extra_bot=""):
    fav_label = ("🗑 Sevimlilardan o'chir" if is_fav else "⭐ Sevimlilarga qo'sh") if lang == "uz" \
        else ("🗑 Удалить из избранного" if is_fav else "⭐ В избранное")
    fav_cb = f"fav_remove_{movie_id}" if is_fav else f"fav_add_{movie_id}"
    rows = [[InlineKeyboardButton(fav_label, callback_data=fav_cb)]]
    rows += _promo_rows(bot_username, channel_username, instagram, extra_bot)
    return InlineKeyboardMarkup(rows)

# ─── KANAL POSTI TUGMALARI ───────────────────────────────────────────────────

def channel_post_keyboard(movie_code="", bot_username="",
                          channel_username="", instagram="", extra_bot=""):
    """Kanaldagi post ostida: 'Kinoni ko'rish' (deep-link) + promo tugmalar."""
    rows = []
    if bot_username and movie_code:
        rows.append([InlineKeyboardButton(
            "🎬 Kinoni ko'rish",
            url=f"https://t.me/{bot_username}?start={movie_code}"
        )])
    if channel_username:
        rows.append([InlineKeyboardButton("📢 Kanalga o'tish", url=f"https://t.me/{channel_username}")])
    if extra_bot:
        rows.append([InlineKeyboardButton("🤖 Yana bir bot", url=f"https://t.me/{extra_bot}")])
    if instagram:
        rows.append([InlineKeyboardButton("📸 Instagram", url=_insta_url(instagram))])
    return InlineKeyboardMarkup(rows) if rows else None

# ─── ADMIN PANEL ─────────────────────────────────────────────────────────────

def admin_main_keyboard(areas=None):
    """areas — ruxsat berilgan bo'limlar to'plami. None bo'lsa — hammasi (owner)."""
    if areas is None:
        areas = {"movies", "channels", "broadcast", "users", "admins", "settings", "stats"}

    btn = {
        "movies":    InlineKeyboardButton("🎬 Kinolar",    callback_data="adm_movies"),
        "channels":  InlineKeyboardButton("📢 Kanallar",   callback_data="adm_channels"),
        "broadcast": InlineKeyboardButton("📨 Broadcast",  callback_data="adm_broadcast"),
        "users":     InlineKeyboardButton("👥 Users",      callback_data="adm_users"),
        "admins":    InlineKeyboardButton("👑 Adminlar",   callback_data="adm_admins"),
        "settings":  InlineKeyboardButton("⚙️ Sozlamalar", callback_data="adm_settings"),
        "stats":     InlineKeyboardButton("📊 Statistika", callback_data="adm_stats"),
    }
    order = ["movies", "channels", "broadcast", "users", "admins", "settings", "stats"]
    visible = [btn[a] for a in order if a in areas]

    # 2 tadan qatorlab joylash
    rows = [visible[i:i + 2] for i in range(0, len(visible), 2)]
    return InlineKeyboardMarkup(rows or [[InlineKeyboardButton("📊 Statistika", callback_data="adm_stats")]])

def admin_movies_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Qo'shish",   callback_data="mov_add"),
            InlineKeyboardButton("📋 Ro'yxat",    callback_data="mov_list_0"),
        ],
        [
            InlineKeyboardButton("🔍 Qidirish",   callback_data="mov_search"),
            InlineKeyboardButton("🔥 TOP",         callback_data="mov_top"),
        ],
        [
            InlineKeyboardButton("🎲 Random yuborish", callback_data="mov_random_send"),
        ],
        [InlineKeyboardButton("🔙 Orqaga",        callback_data="adm_back")],
    ])

def admin_channels_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Qo'shish",   callback_data="ch_add"),
            InlineKeyboardButton("📋 Ro'yxat",    callback_data="ch_list"),
        ],
        [
            InlineKeyboardButton("🔒 Obuna holati", callback_data="ch_toggle_sub"),
        ],
        [InlineKeyboardButton("🔙 Orqaga",        callback_data="adm_back")],
    ])

def admin_users_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👥 Ro'yxat",   callback_data="usr_list_0"),
            InlineKeyboardButton("🔍 Qidirish",  callback_data="usr_search"),
        ],
        [
            InlineKeyboardButton("📥 Export",    callback_data="usr_export"),
        ],
        [InlineKeyboardButton("🔙 Orqaga",       callback_data="adm_back")],
    ])

def admin_settings_keyboard(fwd_block, save_block, bot_username="", channel_username="",
                            post_channel="", instagram="", extra_bot=""):
    fwd_icon  = "✅" if fwd_block  == "1" else "❌"
    save_icon = "✅" if save_block == "1" else "❌"
    bot_label  = f"🤖 Bot: @{bot_username}" if bot_username else "🤖 Bot username (belgilanmagan)"
    ch_label   = f"📢 Kanal: @{channel_username}" if channel_username else "📢 Kanal username (belgilanmagan)"
    post_label = f"📺 Post kanali: {post_channel}" if post_channel else "📺 Post kanali (belgilanmagan)"
    insta_label = f"📸 Instagram: {instagram}" if instagram else "📸 Instagram (belgilanmagan)"
    xbot_label  = f"🎬 Qo'shimcha bot: @{extra_bot}" if extra_bot else "🎬 Qo'shimcha bot (belgilanmagan)"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{fwd_icon} Forward bloklash",  callback_data="set_toggle_forward")],
        [InlineKeyboardButton(f"{save_icon} Saqlash bloklash", callback_data="set_toggle_save")],
        [InlineKeyboardButton(bot_label,                       callback_data="set_bot_username")],
        [InlineKeyboardButton(ch_label,                        callback_data="set_channel_username")],
        [InlineKeyboardButton(post_label,                      callback_data="set_post_channel")],
        [InlineKeyboardButton(insta_label,                     callback_data="set_instagram")],
        [InlineKeyboardButton(xbot_label,                      callback_data="set_extra_bot")],
        [InlineKeyboardButton("🔙 Orqaga",                     callback_data="adm_back")],
    ])

def admin_admins_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Qo'shish",    callback_data="aadm_add"),
            InlineKeyboardButton("📋 Ro'yxat",     callback_data="aadm_list"),
        ],
        [InlineKeyboardButton("🔙 Orqaga",         callback_data="adm_back")],
    ])

def admin_broadcast_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📨 Barchaga",      callback_data="bc_all")],
        [InlineKeyboardButton("👥 Faol userlarga", callback_data="bc_active")],
        [InlineKeyboardButton("🔙 Orqaga",         callback_data="adm_back")],
    ])

def back_admin():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="adm_back")]])

def movie_admin_actions(movie_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"medit_{movie_id}"),
            InlineKeyboardButton("❌ O'chirish",  callback_data=f"mdel_{movie_id}"),
        ],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="mov_list_0")],
    ])

def movie_edit_fields(movie_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Nom",       callback_data=f"mfield_title_{movie_id}")],
        [InlineKeyboardButton("📄 Tavsif",    callback_data=f"mfield_description_{movie_id}")],
        [InlineKeyboardButton("📅 Yil",       callback_data=f"mfield_year_{movie_id}")],
        [InlineKeyboardButton("🎭 Janr",      callback_data=f"mfield_genre_{movie_id}")],
        [InlineKeyboardButton("📂 Kategoriya",callback_data=f"mfield_category_{movie_id}")],
        [InlineKeyboardButton("🔢 Kod",       callback_data=f"mfield_code_{movie_id}")],
        [InlineKeyboardButton("🖼 Poster (rasm)", callback_data=f"mposter_{movie_id}")],
        [InlineKeyboardButton("🔙 Orqaga",    callback_data=f"minfo_{movie_id}")],
    ])
