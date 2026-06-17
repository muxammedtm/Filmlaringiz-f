import asyncio
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
from config import Config
from keyboards import (
    admin_main_keyboard, admin_movies_keyboard, admin_channels_keyboard,
    admin_users_keyboard, admin_settings_keyboard, admin_admins_keyboard,
    admin_broadcast_keyboard, back_admin, movie_admin_actions, movie_edit_fields,
    channel_post_keyboard,
)

db  = Database()
cfg = Config()

ROLES = {
    "super_admin":    "👑 Super Admin",
    "moderator":      "🛡 Moderator",
    "content_admin":  "🎬 Kontent Admin",
    "ads_admin":      "📢 Reklama Admin",
}

# ─── RUXSATLAR (rol → bo'limlar) ─────────────────────────────────────────────
PERMS = {
    "movies":    {"super_admin", "moderator", "content_admin"},
    "users":     {"super_admin", "moderator"},
    "channels":  {"super_admin"},
    "broadcast": {"super_admin", "ads_admin"},
    "admins":    {"super_admin"},
    "settings":  {"super_admin"},
    "stats":     {"super_admin", "moderator", "content_admin", "ads_admin"},
}


def is_admin(user_id: int) -> bool:
    return user_id == cfg.OWNER_ID or user_id in db.get_admin_ids()


def allowed_areas(user_id: int) -> set:
    if user_id == cfg.OWNER_ID:
        return set(PERMS.keys())
    role = db.get_admin_role(user_id)
    if not role:
        return set()
    return {area for area, roles in PERMS.items() if role in roles}


def can(user_id: int, area: str) -> bool:
    if user_id == cfg.OWNER_ID:
        return True
    return area in allowed_areas(user_id)


def _area_for_data(data: str) -> str:
    if data in ("adm_back", "adm_stats"):
        return "stats"
    if data.startswith(("adm_movies", "mov_", "minfo_", "medit_", "mfield_", "mdel_", "mposter_")):
        return "movies"
    if data.startswith(("adm_channels", "ch_")):
        return "channels"
    if data.startswith(("adm_broadcast", "bc_")):
        return "broadcast"
    if data.startswith(("adm_users", "usr_", "uinfo_", "uban_", "uunban_")):
        return "users"
    if data.startswith(("adm_admins", "aadm_")):
        return "admins"
    if data.startswith(("adm_settings", "set_")):
        return "settings"
    return "stats"


def _area_for_state(state: str):
    if state.startswith(("mov_", "mfield_", "mposter_")):
        return "movies"
    if state.startswith("ch_"):
        return "channels"
    if state == "usr_search":
        return "users"
    if state.startswith("broadcast_"):
        return "broadcast"
    if state in ("aadm_add", "aadm_role"):
        return "admins"
    if state.startswith("set_"):
        return "settings"
    return None


def _settings_kb():
    return admin_settings_keyboard(
        db.get_setting("forward_block"),
        db.get_setting("save_block"),
        db.get_setting("bot_username", ""),
        db.get_setting("channel_username", ""),
        db.get_setting("post_channel", ""),
        db.get_setting("instagram", ""),
        db.get_setting("extra_bot", ""),
    )


def _panel_text(s):
    return (
        f"👑 <b>Admin Panel</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Foydalanuvchilar: <b>{s['users']}</b>\n"
        f"📈 Bugun qo'shilganlar: <b>{s['today_users']}</b>\n"
        f"🎬 Kinolar: <b>{s['movies']}</b>\n"
        f"📢 Kanallar: <b>{s['channels']}</b>\n"
        f"👑 Adminlar: <b>{s['admins']}</b>\n"
    )


# ─── /admin ──────────────────────────────────────────────────────────────────

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return
    s = db.get_stats()
    await update.message.reply_text(
        _panel_text(s), parse_mode="HTML",
        reply_markup=admin_main_keyboard(allowed_areas(user.id))
    )


# ─── ADMIN CALLBACK DISPATCHER ───────────────────────────────────────────────

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.message.edit_text("❌ Ruxsat yo'q!")
        return

    data = query.data

    # ── Ruxsat tekshiruvi (rol bo'yicha) ─────────────────────────────────────
    area = _area_for_data(data)
    if not can(user_id, area):
        await query.answer("❌ Bu bo'limga ruxsatingiz yo'q!", show_alert=True)
        return

    # ── Asosiy panel ──────────────────────────────────────────────────────────
    if data == "adm_back":
        s = db.get_stats()
        await query.message.edit_text(
            _panel_text(s), parse_mode="HTML",
            reply_markup=admin_main_keyboard(allowed_areas(user_id))
        )

    # ── Statistika ────────────────────────────────────────────────────────────
    elif data == "adm_stats":
        s = db.get_stats()
        text = (
            f"📊 <b>Bot Statistikasi</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Jami foydalanuvchilar: <b>{s['users']}</b>\n"
            f"📈 Bugungi yangilar: <b>{s['today_users']}</b>\n"
            f"🎬 Jami kinolar: <b>{s['movies']}</b>\n"
            f"📢 Aktiv kanallar: <b>{s['channels']}</b>\n"
            f"👑 Adminlar: <b>{s['admins']}</b>\n"
        )
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=back_admin())

    # ── KINOLAR ───────────────────────────────────────────────────────────────
    elif data == "adm_movies":
        await query.message.edit_text("🎬 <b>Kino boshqaruvi</b>", parse_mode="HTML",
                                       reply_markup=admin_movies_keyboard())

    elif data == "mov_add":
        context.user_data["adm_state"] = "mov_title"
        await query.message.edit_text(
            "🎬 <b>Kino qo'shish</b>\n\n1️⃣ Film nomini yuboring:",
            parse_mode="HTML", reply_markup=back_admin()
        )

    elif data.startswith("mov_list_"):
        offset = int(data.split("_")[-1])
        movies = db.get_all_movies(limit=10, offset=offset)
        if not movies:
            await query.message.edit_text("🎬 Kinolar yo'q.", reply_markup=back_admin())
            return
        text = f"🎬 <b>Kinolar ro'yxati</b> ({offset+1}–{offset+len(movies)}):\n━━━━━━━━━━━━━━━━━━━━\n"
        kb = []
        for m in movies:
            text += f"• <code>{m['code']}</code> — {m['title']} 👁{m['views']}\n"
            kb.append([InlineKeyboardButton(
                f"🎬 {m['title'][:25]}", callback_data=f"minfo_{m['id']}"
            )])
        nav = []
        if offset > 0:
            nav.append(InlineKeyboardButton("⬅️", callback_data=f"mov_list_{offset-10}"))
        if len(movies) == 10:
            nav.append(InlineKeyboardButton("➡️", callback_data=f"mov_list_{offset+10}"))
        if nav:
            kb.append(nav)
        kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data="adm_movies")])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("minfo_"):
        movie_id = int(data.split("_")[1])
        m = db.get_movie_by_id(movie_id)
        if not m:
            await query.message.edit_text("❌ Kino topilmadi.", reply_markup=back_admin())
            return
        poster = "✅ Bor" if m.get("poster_id") else "❌ Yo'q"
        text = (
            f"🎬 <b>{m['title']}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 Kod: <code>{m['code']}</code>\n"
            f"📅 Yil: {m.get('year') or '—'}\n"
            f"🎭 Janr: {m.get('genre') or '—'}\n"
            f"📂 Kategoriya: {m.get('category') or '—'}\n"
            f"🖼 Poster: {poster}\n"
            f"👁 Ko'rilgan: {m['views']}\n"
            f"🗓 Qo'shilgan: {m.get('added_at','')[:10]}\n"
        )
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=movie_admin_actions(movie_id))

    elif data.startswith("medit_"):
        movie_id = int(data.split("_")[1])
        await query.message.edit_text(
            "✏️ <b>Qaysi maydonni tahrirlash?</b>", parse_mode="HTML",
            reply_markup=movie_edit_fields(movie_id)
        )

    elif data.startswith("mposter_"):
        movie_id = int(data.split("_")[1])
        context.user_data["adm_state"] = f"mposter_{movie_id}"
        await query.message.edit_text(
            "🖼 <b>Poster (rasm) yangilash</b>\n\n"
            "Yangi rasmni yuboring.\n"
            "O'chirish uchun: /clear",
            parse_mode="HTML", reply_markup=back_admin()
        )

    elif data.startswith("mfield_"):
        parts = data.split("_")
        field = parts[1]
        movie_id = int(parts[2])
        context.user_data["adm_state"] = f"mfield_{field}_{movie_id}"
        labels = {
            "title": "Yangi nomni", "description": "Yangi tavsifni",
            "year": "Yangi yilni", "genre": "Yangi janrni",
            "category": "Yangi kategoriyani", "code": "Yangi kodni"
        }
        await query.message.edit_text(
            f"✏️ {labels.get(field, field)} yuboring:", reply_markup=back_admin()
        )

    elif data.startswith("mdel_"):
        movie_id = int(data.split("_")[1])
        db.delete_movie(movie_id)
        await query.message.edit_text(
            "✅ Kino o'chirildi!", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Ro'yxat", callback_data="mov_list_0")
            ]])
        )

    elif data == "mov_search":
        context.user_data["adm_state"] = "mov_search"
        await query.message.edit_text("🔍 Kino nomi yoki kodini yuboring:", reply_markup=back_admin())

    elif data == "mov_top":
        top = db.get_top_movies(10)
        text = "🔥 <b>TOP 10 kinolar:</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        for i, m in enumerate(top, 1):
            text += f"{i}. {m['title']} — Kod: <code>{m['code']}</code> 👁{m['views']}\n"
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=back_admin())

    elif data == "mov_random_send":
        import random as _rand
        ids = db.get_all_movies_ids()
        if not ids:
            await query.message.edit_text("📭 Hozircha kinolar yo'q.", reply_markup=back_admin())
        else:
            movie = db.get_movie_by_id(_rand.choice(ids))
            await query.message.edit_text(
                f"🔀 <b>Tasodifiy kino tanlandi!</b>\n\n"
                f"🎬 <b>{movie['title']}</b>\n"
                f"🆔 Kod: <code>{movie['code']}</code>\n\n"
                "Foydalanuvchilarga yuborish uchun broadcast ishlating.",
                parse_mode="HTML", reply_markup=back_admin()
            )

    # ── KANALLAR ──────────────────────────────────────────────────────────────
    elif data == "adm_channels":
        await query.message.edit_text("📢 <b>Kanal boshqaruvi</b>", parse_mode="HTML",
                                       reply_markup=admin_channels_keyboard())

    elif data == "ch_add":
        context.user_data["adm_state"] = "ch_add"
        await query.message.edit_text(
            "📢 <b>Kanal qo'shish</b>\n\n"
            "Kanal username yoki invite linkini yuboring:\n\n"
            "📌 <b>Ochiq kanal:</b> <code>@kanalname</code>\n"
            "📌 <b>Yopiq kanal:</b> <code>https://t.me/+XhDl2wJvCVtiZjZi</code>\n\n"
            "⚠️ Yopiq kanalda bot admin bo'lishi shart!",
            parse_mode="HTML", reply_markup=back_admin()
        )

    elif data == "ch_list":
        channels = db.get_all_channels()
        if not channels:
            await query.message.edit_text("Kanallar yo'q.", reply_markup=back_admin())
            return
        text = "Barcha kanallar:\n\n"
        kb = []
        for ch in channels:
            icon    = "🟢" if ch["is_active"] else "🔴"
            lim     = ch["limit_count"]
            joined  = ch["joined_count"]
            title   = ch["title"]
            lim_str = " (" + str(joined) + "/" + str(lim) + ")" if lim > 0 else ""
            text += icon + " " + title + lim_str + "\n"
            kb.append([
                InlineKeyboardButton(icon + " " + title[:20] + lim_str, callback_data="ch_info_" + str(ch["id"]))
            ])
        kb.append([InlineKeyboardButton("Orqaga", callback_data="adm_channels")])
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("ch_info_"):
        ch_id = int(data.split("_")[-1])
        ch = db.get_channel_by_id(ch_id)
        if not ch:
            await query.message.edit_text("Topilmadi.", reply_markup=back_admin())
            return
        status  = "🟢 Faol" if ch["is_active"] else "🔴 To'xtatilgan"
        lim     = ch["limit_count"]
        joined  = ch["joined_count"]
        lim_str = str(joined) + "/" + str(lim) if lim > 0 else "Cheksiz"
        text = (
            "Kanal: <b>" + ch["title"] + "</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Holat: " + status + "\n"
            "Obunachi: <b>" + lim_str + "</b>\n"
        )
        kb = []
        if ch["is_active"]:
            kb.append([InlineKeyboardButton("🔴 To'xtatish", callback_data="ch_off_" + str(ch_id))])
        else:
            kb.append([InlineKeyboardButton("🟢 Qayta yoqish", callback_data="ch_on_" + str(ch_id))])
        kb.append([InlineKeyboardButton("❌ O'chirish", callback_data="ch_del_" + str(ch_id))])
        kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data="ch_list")])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("ch_off_"):
        ch_id = int(data.split("_")[-1])
        db.deactivate_channel(ch_id)
        await query.message.edit_text("🔴 Kanal to'xtatildi.", reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Kanallar", callback_data="ch_list")
        ]]))

    elif data.startswith("ch_on_"):
        ch_id = int(data.split("_")[-1])
        db.activate_channel(ch_id)
        await query.message.edit_text("🟢 Kanal qayta yoqildi (hisob 0 dan).", reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Kanallar", callback_data="ch_list")
        ]]))

    elif data.startswith("ch_del_"):
        ch_id = int(data.split("_")[-1])
        db.delete_channel(ch_id)
        await query.message.edit_text("❌ Kanal o'chirildi.", reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Kanallar", callback_data="ch_list")
        ]]))

    elif data == "ch_toggle_sub":
        cur = db.get_setting("sub_required")
        db.set_setting("sub_required", "0" if cur == "1" else "1")
        now = db.get_setting("sub_required")
        state_txt = "🟢 YOQILDI" if now == "1" else "🔴 O'CHIRILDI"
        await query.message.edit_text(
            f"🔒 Majburiy obuna: <b>{state_txt}</b>", parse_mode="HTML",
            reply_markup=admin_channels_keyboard()
        )

    # ── BROADCAST ─────────────────────────────────────────────────────────────
    elif data == "adm_broadcast":
        await query.message.edit_text(
            "📨 <b>Xabar yuborish</b>\n\nKimga yubormoqchisiz?",
            parse_mode="HTML", reply_markup=admin_broadcast_keyboard()
        )

    elif data in ("bc_all", "bc_active"):
        context.user_data["adm_state"] = f"broadcast_{data}"
        label = "Barcha foydalanuvchilarga" if data == "bc_all" else "So'nggi 7 kun faol userlarga"
        await query.message.edit_text(
            f"📨 <b>{label}</b> yuboriladigan xabarni yuboring:\n\n"
            f"<i>Matn, rasm, video yoki dokument bo'lishi mumkin.</i>\n"
            f"❌ Bekor qilish: /cancel",
            parse_mode="HTML", reply_markup=back_admin()
        )

    # ── USERS ────────────────────────────────────────────────────────────────
    elif data == "adm_users":
        await query.message.edit_text("👥 <b>Foydalanuvchilar</b>", parse_mode="HTML",
                                       reply_markup=admin_users_keyboard())

    elif data.startswith("usr_list_"):
        offset = int(data.split("_")[-1])
        users = db.get_all_users_info(limit=10, offset=offset)
        if not users:
            await query.message.edit_text("👥 Foydalanuvchilar yo'q.", reply_markup=back_admin())
            return
        text = f"👥 <b>Foydalanuvchilar</b> ({offset+1}–{offset+len(users)}):\n━━━━━━━━━━━━━━━━━━━━\n"
        kb = []
        for u in users:
            ban_icon = "🚫" if u["is_banned"] else "✅"
            uname = f"@{u['username']}" if u["username"] else u["first_name"]
            text += f"{ban_icon} {uname} (<code>{u['user_id']}</code>)\n"
            kb.append([InlineKeyboardButton(
                f"{ban_icon} {uname[:20]}", callback_data=f"uinfo_{u['user_id']}"
            )])
        nav = []
        if offset > 0:
            nav.append(InlineKeyboardButton("⬅️", callback_data=f"usr_list_{offset-10}"))
        if len(users) == 10:
            nav.append(InlineKeyboardButton("➡️", callback_data=f"usr_list_{offset+10}"))
        if nav:
            kb.append(nav)
        kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data="adm_users")])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("uinfo_"):
        uid = int(data.split("_")[1])
        u = db.get_user(uid)
        if not u:
            await query.message.edit_text("❌ Topilmadi.", reply_markup=back_admin())
            return
        ban_icon = "🚫 BAN" if u["is_banned"] else "✅ Aktiv"
        uname = f"@{u['username']}" if u["username"] else "—"
        text = (
            f"👤 <b>Foydalanuvchi</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 ID: <code>{u['user_id']}</code>\n"
            f"👤 Ism: {u['first_name']}\n"
            f"📛 Username: {uname}\n"
            f"🌐 Til: {u['lang']}\n"
            f"📅 Qo'shilgan: {u['joined_at']}\n"
            f"⚡ Holat: {ban_icon}\n"
        )
        ban_cb = f"uunban_{uid}" if u["is_banned"] else f"uban_{uid}"
        ban_label = "✅ Unban" if u["is_banned"] else "🚫 Ban"
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(ban_label, callback_data=ban_cb)],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="usr_list_0")],
        ]))

    elif data.startswith("uban_"):
        uid = int(data.split("_")[1])
        db.ban_user(uid)
        await query.message.edit_text(f"🚫 User <code>{uid}</code> ban qilindi.", parse_mode="HTML",
                                       reply_markup=back_admin())

    elif data.startswith("uunban_"):
        uid = int(data.split("_")[1])
        db.unban_user(uid)
        await query.message.edit_text(f"✅ User <code>{uid}</code> unban qilindi.", parse_mode="HTML",
                                       reply_markup=back_admin())

    elif data == "usr_search":
        context.user_data["adm_state"] = "usr_search"
        await query.message.edit_text("🔍 Foydalanuvchi ID, username yoki ismini yuboring:", reply_markup=back_admin())

    elif data == "usr_export":
        await _export_users(query, context)

    # ── SOZLAMALAR ───────────────────────────────────────────────────────────
    elif data == "adm_settings":
        await query.message.edit_text("⚙️ <b>Sozlamalar</b>", parse_mode="HTML", reply_markup=_settings_kb())

    elif data == "set_toggle_forward":
        cur = db.get_setting("forward_block")
        db.set_setting("forward_block", "0" if cur == "1" else "1")
        await query.message.edit_reply_markup(_settings_kb())

    elif data == "set_toggle_save":
        cur = db.get_setting("save_block")
        db.set_setting("save_block", "0" if cur == "1" else "1")
        await query.message.edit_reply_markup(_settings_kb())

    elif data == "set_bot_username":
        context.user_data["adm_state"] = "set_bot_username"
        cur = db.get_setting("bot_username", "")
        cur_text = f"\n\nHozirgi: <code>@{cur}</code>" if cur else ""
        await query.message.edit_text(
            f"🤖 <b>Bot username</b>{cur_text}\n\n"
            f"Bot username ini yuboring (@ belgisisiz):\n"
            f"<i>Masalan: KinoUzBot</i>",
            parse_mode="HTML", reply_markup=back_admin()
        )

    elif data == "set_channel_username":
        context.user_data["adm_state"] = "set_channel_username"
        cur = db.get_setting("channel_username", "")
        cur_text = f"\n\nHozirgi: <code>@{cur}</code>" if cur else ""
        await query.message.edit_text(
            f"📢 <b>Kanal username</b>{cur_text}\n\n"
            f"Kanal username ini yuboring (@ belgisisiz):\n"
            f"<i>Masalan: KinoUzChannel</i>",
            parse_mode="HTML", reply_markup=back_admin()
        )

    elif data == "set_post_channel":
        context.user_data["adm_state"] = "set_post_channel"
        cur = db.get_setting("post_channel", "")
        cur_text = f"\n\nHozirgi: <code>{cur}</code>" if cur else ""
        await query.message.edit_text(
            f"📺 <b>Post kanali ID</b>{cur_text}\n\n"
            f"Kanal ID sini yuboring:\n"
            f"<i>Masalan: -1001234567890</i>\n\n"
            f"<b>ID ni topish:</b>\n"
            f"1. @getidsbot ga kanaldan forward qiling\n"
            f"2. Bot javob beradi: Chat ID: -1001234567890",
            parse_mode="HTML", reply_markup=back_admin()
        )

    elif data == "set_instagram":
        context.user_data["adm_state"] = "set_instagram"
        cur = db.get_setting("instagram", "")
        cur_text = f"\n\nHozirgi: <code>{cur}</code>" if cur else ""
        await query.message.edit_text(
            f"📸 <b>Instagram sahifa</b>{cur_text}\n\n"
            f"Instagram username yoki to'liq linkni yuboring:\n"
            f"<i>Masalan: kino_uz</i>  yoki  <i>https://instagram.com/kino_uz</i>\n\n"
            f"O'chirish uchun: /clear",
            parse_mode="HTML", reply_markup=back_admin()
        )

    elif data == "set_extra_bot":
        context.user_data["adm_state"] = "set_extra_bot"
        cur = db.get_setting("extra_bot", "")
        cur_text = f"\n\nHozirgi: <code>@{cur}</code>" if cur else ""
        await query.message.edit_text(
            f"🎬 <b>Qo'shimcha Telegram bot</b>{cur_text}\n\n"
            f"Bot username ini yuboring (@ belgisisiz):\n"
            f"<i>Masalan: IkkinchiKinoBot</i>\n\n"
            f"O'chirish uchun: /clear",
            parse_mode="HTML", reply_markup=back_admin()
        )

    # ── ADMINLAR ─────────────────────────────────────────────────────────────
    elif data == "adm_admins":
        await query.message.edit_text("👑 <b>Adminlar</b>", parse_mode="HTML",
                                       reply_markup=admin_admins_keyboard())

    elif data == "aadm_add":
        context.user_data["adm_state"] = "aadm_add"
        await query.message.edit_text(
            "👑 <b>Admin qo'shish</b>\n\n"
            "Yangi admin Telegram ID sini yuboring.\n"
            "Keyin rolni tanlang:\n\n"
            "Rollar: <code>super_admin</code>, <code>moderator</code>, <code>content_admin</code>, <code>ads_admin</code>",
            parse_mode="HTML", reply_markup=back_admin()
        )

    elif data == "aadm_list":
        admins = db.get_admins()
        if not admins:
            await query.message.edit_text("👑 Adminlar yo'q.", reply_markup=back_admin())
            return
        text = "👑 <b>Adminlar ro'yxati:</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        kb = []
        for a in admins:
            role_label = ROLES.get(a["role"], a["role"])
            text += f"• <code>{a['user_id']}</code> — {role_label}\n"
            if a["user_id"] != cfg.OWNER_ID:
                kb.append([InlineKeyboardButton(
                    f"🗑 {a['user_id']}", callback_data=f"aadm_del_{a['user_id']}"
                )])
        kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data="adm_admins")])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("aadm_del_"):
        uid = int(data.split("_")[-1])
        db.remove_admin(uid)
        await query.message.edit_text(f"✅ Admin <code>{uid}</code> o'chirildi.", parse_mode="HTML",
                                       reply_markup=InlineKeyboardMarkup([[
                                           InlineKeyboardButton("🔙 Adminlar", callback_data="aadm_list")
                                       ]]))

    elif data.startswith("aadm_role_"):
        parts = data.split("_")
        role = parts[2]
        uid  = int(parts[3])
        db.add_admin(uid, role)
        await query.message.edit_text(
            f"✅ Admin qo'shildi!\n🆔 <code>{uid}</code>\n🔐 Rol: {ROLES.get(role, role)}",
            parse_mode="HTML", reply_markup=back_admin()
        )


# ─── ADMIN STATE HANDLER ─────────────────────────────────────────────────────

async def admin_state_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return
    state = context.user_data.get("adm_state", "")
    if not state:
        return False  # boshqa handler ishlaydi

    # Rol bo'yicha ruxsat tekshiruvi
    area = _area_for_state(state)
    if area and not can(user.id, area):
        context.user_data.pop("adm_state", None)
        await update.message.reply_text("❌ Bu amalga ruxsatingiz yo'q!")
        return True

    msg   = update.message
    text  = msg.text.strip() if msg.text else ""

    # ─── KINO QO'SHISH ────────────────────────────────────────────────────────
    if state == "mov_title":
        context.user_data["new_movie"] = {"title": text, "description": "", "year": "", "genre": "", "category": ""}
        context.user_data["adm_state"] = "mov_desc"
        await msg.reply_text("2️⃣ Tavsif yuboring (yoki /skip):")
        return True

    elif state == "mov_desc":
        if text != "/skip":
            context.user_data["new_movie"]["description"] = text
        context.user_data["adm_state"] = "mov_year"
        await msg.reply_text("3️⃣ Yilni yuboring (yoki /skip):")
        return True

    elif state == "mov_year":
        if text != "/skip":
            context.user_data["new_movie"]["year"] = text
        context.user_data["adm_state"] = "mov_genre"
        await msg.reply_text("4️⃣ Janrni yuboring (yoki /skip):")
        return True

    elif state == "mov_genre":
        if text != "/skip":
            context.user_data["new_movie"]["genre"] = text
        context.user_data["adm_state"] = "mov_category"
        await msg.reply_text("5️⃣ Kategoriyani yuboring (yoki /skip):")
        return True

    elif state == "mov_category":
        if text != "/skip":
            context.user_data["new_movie"]["category"] = text
        context.user_data["adm_state"] = "mov_code"
        await msg.reply_text("6️⃣ Kino kodini kiriting (masalan: <code>001</code>):", parse_mode="HTML")
        return True

    elif state == "mov_code":
        if db.get_movie_by_code(text):
            await msg.reply_text(f"❌ Bu kod mavjud: <code>{text}</code>. Boshqa kod kiriting:", parse_mode="HTML")
            return True
        context.user_data["new_movie"]["code"] = text
        context.user_data["adm_state"] = "mov_file"
        await msg.reply_text("7️⃣ Kino faylini (video yoki dokument) yuboring:")
        return True

    elif state == "mov_file":
        file_id = None
        if msg.video:
            file_id = msg.video.file_id
        elif msg.document:
            file_id = msg.document.file_id
        if not file_id:
            await msg.reply_text("❌ Faqat video yoki dokument yuboring!")
            return True
        context.user_data["new_movie"]["file_id"] = file_id
        context.user_data["adm_state"] = "mov_poster"
        await msg.reply_text(
            "8️⃣ Endi kino <b>POSTERINI</b> (rasm / skrinshot) yuboring.\n\n"
            "Bu rasm kanalga post bo'lib chiqadi.\n"
            "Rasmsiz qoldirish uchun: /skip",
            parse_mode="HTML"
        )
        return True

    elif state == "mov_poster":
        poster_id = ""
        if msg.photo:
            poster_id = msg.photo[-1].file_id
        elif text == "/skip":
            poster_id = ""
        else:
            await msg.reply_text("❌ Rasm (poster) yuboring yoki /skip bosing.")
            return True

        movie = context.user_data.pop("new_movie")
        movie["poster_id"] = poster_id
        context.user_data.pop("adm_state", None)
        db.add_movie(movie)

        # Kanalga post (poster + 'Kinoni ko'rish' tugmasi)
        posted = await _post_to_channel(context.bot, movie)

        extra = "📺 Kanalga post chiqdi.\n" if posted else ""
        if not poster_id:
            extra += "ℹ️ Poster yuborilmadi — kanalga faqat matn chiqdi.\n"
        await msg.reply_text(
            f"✅ <b>Kino qo'shildi!</b>\n"
            f"🎬 {movie['title']}\n"
            f"🆔 Kod: <code>{movie['code']}</code>\n"
            f"{extra}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📋 Kinolar ro'yxati", callback_data="mov_list_0")
            ]])
        )
        return True

    # ─── POSTER TAHRIRLASH ────────────────────────────────────────────────────
    elif state.startswith("mposter_"):
        movie_id = int(state.split("_")[1])
        if msg.photo:
            db.update_movie(movie_id, "poster_id", msg.photo[-1].file_id)
            context.user_data.pop("adm_state", None)
            await msg.reply_text("✅ Poster yangilandi!", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kinoga qaytish", callback_data=f"minfo_{movie_id}")
            ]]))
        elif text == "/clear":
            db.update_movie(movie_id, "poster_id", "")
            context.user_data.pop("adm_state", None)
            await msg.reply_text("🗑 Poster o'chirildi.", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kinoga qaytish", callback_data=f"minfo_{movie_id}")
            ]]))
        else:
            await msg.reply_text("❌ Rasm yuboring yoki /clear bilan o'chiring.")
        return True

    # ─── KINO TAHRIRLASH (matnli maydonlar) ───────────────────────────────────
    elif state.startswith("mfield_"):
        parts   = state.split("_")
        field   = parts[1]
        movie_id = int(parts[2])
        db.update_movie(movie_id, field, text)
        context.user_data.pop("adm_state", None)
        m = db.get_movie_by_id(movie_id)
        await msg.reply_text(
            f"✅ {field} yangilandi!\n🎬 {m['title'] if m else ''}", parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kinoga qaytish", callback_data=f"minfo_{movie_id}")
            ]])
        )
        return True

    # ─── KINO QIDIRISH ────────────────────────────────────────────────────────
    elif state == "mov_search":
        context.user_data.pop("adm_state", None)
        results = db.search_movies(text)
        if not results:
            await msg.reply_text("❌ Natija topilmadi.", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="adm_movies")
            ]]))
            return True
        kb = [[InlineKeyboardButton(
            f"🎬 {m['title'][:30]} [{m['code']}]", callback_data=f"minfo_{m['id']}"
        )] for m in results]
        kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data="adm_movies")])
        await msg.reply_text(
            f"🔍 <b>{len(results)} ta natija:</b>", parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return True

    # ─── KANAL QO'SHISH ───────────────────────────────────────────────────────
    elif state == "ch_add":
        context.user_data.pop("adm_state", None)
        invite_link = ""

        if text.startswith("https://t.me/+") or text.startswith("t.me/+"):
            invite_link = text if text.startswith("https://") else "https://" + text
            context.user_data["adm_state"]  = "ch_add_private_id"
            context.user_data["ch_invite"]  = invite_link
            await msg.reply_text(
                "Yopiq kanal — Kanal ID sini yuboring.\n\n"
                "Kanal ID topish:\n"
                "1. @getidsbot ga kanaldan forward qiling\n\n"
                "Masalan: -1001234567890",
                reply_markup=back_admin()
            )
            return True

        username = text if text.startswith("@") else "@" + text
        try:
            chat = await context.bot.get_chat(username)
            title = chat.title or username
            context.user_data["ch_pending"] = {
                "channel_id": str(chat.id),
                "username":   username,
                "title":      title,
                "invite_link": ""
            }
            context.user_data["adm_state"] = "ch_add_limit"
            await msg.reply_text(
                "Kanal topildi: <b>" + title + "</b>\n\n"
                "Nechta obunachidan keyin bu kanal majburiy obunadan olib tashlansin?\n\n"
                "Cheksiz qoldirish: 0 yuboring\n"
                "Masalan: 50, 100, 500",
                parse_mode="HTML",
                reply_markup=back_admin()
            )
        except Exception as e:
            await msg.reply_text(
                "Xatolik: " + str(e) + "\n\n"
                "Bot kanalga admin qilinganmi?\n"
                "Username to'g'rimi?"
            )
        return True

    # ─── YOPIQ KANAL ID ───────────────────────────────────────────────────────
    elif state == "ch_add_private_id":
        invite_link = context.user_data.pop("ch_invite", "")
        raw = text.strip()
        if not raw.lstrip("-").isdigit():
            await msg.reply_text("Noto'g'ri ID! Masalan: -1001234567890")
            return True
        channel_id = raw if raw.startswith("-") else "-100" + raw
        try:
            chat = await context.bot.get_chat(int(channel_id))
            title = chat.title or "Yopiq kanal"
            context.user_data["ch_pending"] = {
                "channel_id":  channel_id,
                "username":    invite_link,
                "title":       title,
                "invite_link": invite_link
            }
            context.user_data["adm_state"] = "ch_add_limit"
            await msg.reply_text(
                "Kanal topildi: <b>" + title + "</b>\n\n"
                "Nechta obunachidan keyin bu kanal majburiy obunadan olib tashlansin?\n\n"
                "Cheksiz qoldirish: 0 yuboring\n"
                "Masalan: 50, 100, 500",
                parse_mode="HTML",
                reply_markup=back_admin()
            )
        except Exception as e:
            await msg.reply_text(
                "Xatolik: " + str(e) + "\n\n"
                "Bot kanalga admin qilinganmi?\n"
                "Kanal ID to'g'rimi: " + channel_id
            )
        return True

    # ─── KANAL LIMIT ─────────────────────────────────────────────────────────
    elif state == "ch_add_limit":
        try:
            limit = int(text.strip())
        except ValueError:
            await msg.reply_text("Faqat raqam yuboring! Masalan: 50")
            return True

        ch = context.user_data.pop("ch_pending", None)
        context.user_data.pop("adm_state", None)
        if not ch:
            await msg.reply_text("Xatolik! Qaytadan urining.")
            return True

        db.add_channel(
            ch["channel_id"], ch["username"],
            ch["title"], ch["invite_link"], limit
        )
        lim_text = str(limit) + " ta obunachidan keyin to'xtatiladi" if limit > 0 else "Cheksiz"
        await msg.reply_text(
            "Kanal qo'shildi!\n\n"
            "Nom: <b>" + ch["title"] + "</b>\n"
            "Limit: <b>" + lim_text + "</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Kanallar", callback_data="ch_list")
            ]])
        )
        return True

    # ─── USER QIDIRISH ────────────────────────────────────────────────────────
    elif state == "usr_search":
        context.user_data.pop("adm_state", None)
        results = db.search_user(text)
        if not results:
            await msg.reply_text("❌ Topilmadi.", reply_markup=back_admin())
            return True
        kb = [[InlineKeyboardButton(
            f"{'🚫' if u['is_banned'] else '✅'} {u['first_name'] or u['user_id']}",
            callback_data=f"uinfo_{u['user_id']}"
        )] for u in results]
        kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data="adm_users")])
        await msg.reply_text(
            f"🔍 <b>{len(results)} ta natija:</b>", parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return True

    # ─── BROADCAST ───────────────────────────────────────────────────────────
    elif state.startswith("broadcast_"):
        bc_type = state.split("_")[-1]
        context.user_data.pop("adm_state", None)
        if text == "/cancel":
            await msg.reply_text("❌ Bekor qilindi.", reply_markup=back_admin())
            return True
        user_ids = db.get_all_user_ids() if bc_type == "all" else db.get_active_user_ids()
        total = len(user_ids)
        status_msg = await msg.reply_text(f"📨 Yuborilmoqda... 0/{total}")
        sent = failed = 0
        for i, uid in enumerate(user_ids):
            try:
                if msg.text:
                    await context.bot.send_message(uid, msg.text, parse_mode="HTML")
                elif msg.photo:
                    await context.bot.send_photo(uid, msg.photo[-1].file_id,
                                                  caption=msg.caption or "", parse_mode="HTML")
                elif msg.video:
                    await context.bot.send_video(uid, msg.video.file_id,
                                                  caption=msg.caption or "", parse_mode="HTML")
                elif msg.document:
                    await context.bot.send_document(uid, msg.document.file_id,
                                                     caption=msg.caption or "", parse_mode="HTML")
                sent += 1
            except Exception:
                failed += 1
            if (i + 1) % 50 == 0:
                try:
                    await status_msg.edit_text(f"📨 Yuborilmoqda... {i+1}/{total}")
                except Exception:
                    pass
            await asyncio.sleep(0.05)

        await status_msg.edit_text(
            f"✅ <b>Broadcast tugadi!</b>\n\n"
            f"📨 Yuborildi: <b>{sent}</b>\n"
            f"❌ Xato: <b>{failed}</b>\n"
            f"👥 Jami: <b>{total}</b>",
            parse_mode="HTML"
        )
        return True

    # ─── ADMIN QO'SHISH ───────────────────────────────────────────────────────
    elif state == "aadm_add":
        try:
            new_id = int(text.strip())
            context.user_data["aadm_pending_id"] = new_id
            context.user_data["adm_state"] = "aadm_role"
            kb = [[InlineKeyboardButton(label, callback_data=f"aadm_role_{role}_{new_id}")]
                  for role, label in ROLES.items()]
            kb.append([InlineKeyboardButton("🔙 Bekor qilish", callback_data="adm_admins")])
            await msg.reply_text(
                f"👑 ID: <code>{new_id}</code>\n\nRolni tanlang:",
                parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb)
            )
        except ValueError:
            await msg.reply_text("❌ Noto'g'ri ID! Faqat raqam yuboring.")
        return True

    # ─── BOT USERNAME ─────────────────────────────────────────────────────────
    elif state == "set_bot_username":
        context.user_data.pop("adm_state", None)
        val = text.lstrip("@").strip()
        db.set_setting("bot_username", val)
        await msg.reply_text(
            f"✅ Bot username saqlandi: <code>@{val}</code>",
            parse_mode="HTML", reply_markup=_settings_kb()
        )
        return True

    # ─── KANAL USERNAME ───────────────────────────────────────────────────────
    elif state == "set_channel_username":
        context.user_data.pop("adm_state", None)
        val = text.lstrip("@").strip()
        db.set_setting("channel_username", val)
        await msg.reply_text(
            f"✅ Kanal username saqlandi: <code>@{val}</code>",
            parse_mode="HTML", reply_markup=_settings_kb()
        )
        return True

    # ─── POST KANALI ──────────────────────────────────────────────────────────
    elif state == "set_post_channel":
        context.user_data.pop("adm_state", None)
        val = text.strip()
        db.set_setting("post_channel", val)
        await msg.reply_text(
            f"✅ Post kanali ID saqlandi: <code>{val}</code>",
            parse_mode="HTML", reply_markup=_settings_kb()
        )
        return True

    # ─── INSTAGRAM ────────────────────────────────────────────────────────────
    elif state == "set_instagram":
        context.user_data.pop("adm_state", None)
        val = "" if text == "/clear" else text.strip()
        db.set_setting("instagram", val)
        shown = val if val else "(o'chirildi)"
        await msg.reply_text(
            f"✅ Instagram saqlandi: <code>{shown}</code>",
            parse_mode="HTML", reply_markup=_settings_kb()
        )
        return True

    # ─── QO'SHIMCHA BOT ───────────────────────────────────────────────────────
    elif state == "set_extra_bot":
        context.user_data.pop("adm_state", None)
        val = "" if text == "/clear" else text.lstrip("@").strip()
        db.set_setting("extra_bot", val)
        shown = f"@{val}" if val else "(o'chirildi)"
        await msg.reply_text(
            f"✅ Qo'shimcha bot saqlandi: <code>{shown}</code>",
            parse_mode="HTML", reply_markup=_settings_kb()
        )
        return True

    return False


# ─── KANALGA POST ────────────────────────────────────────────────────────────

async def _post_to_channel(bot, movie: dict) -> bool:
    """Kanalga kino POSTERINI (rasm) + 'Kinoni ko'rish' tugmasi bilan joylaydi.
    Tugma bosilganda foydalanuvchi botga kiradi va kino avtomatik yuboriladi."""
    post_channel = db.get_setting("post_channel", "").strip()
    if not post_channel:
        return False

    bot_username     = db.get_setting("bot_username", "").strip() or cfg.BOT_USERNAME
    channel_username = db.get_setting("channel_username", "").strip()
    instagram        = db.get_setting("instagram", "").strip()
    extra_bot        = db.get_setting("extra_bot", "").strip()

    text = f"🎬 <b>{movie['title']}</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    if movie.get("description"):
        text += f"📝 {movie['description']}\n"
    if movie.get("year"):
        text += f"📅 Yil: {movie['year']}\n"
    if movie.get("genre"):
        text += f"🎭 Janr: {movie['genre']}\n"
    if movie.get("category"):
        text += f"📂 Kategoriya: {movie['category']}\n"
    text += f"\n🆔 Kod: <code>{movie['code']}</code>"

    footer = []
    if bot_username:
        footer.append(f"🤖 Bot: @{bot_username}")
    if channel_username:
        footer.append(f"📢 Kanal: @{channel_username}")
    if extra_bot:
        footer.append(f"🎬 @{extra_bot}")
    if instagram:
        footer.append(f"📸 {instagram}")
    if footer:
        text += "\n━━━━━━━━━━━━━━━━━━━━\n" + "  |  ".join(footer)
    text += "\n\n👇 Kinoni ko'rish uchun tugmani bosing"

    kb = channel_post_keyboard(
        movie_code=movie.get("code", ""),
        bot_username=bot_username,
        channel_username=channel_username,
        instagram=instagram,
        extra_bot=extra_bot,
    )

    poster = movie.get("poster_id", "")
    try:
        if poster:
            await bot.send_photo(
                chat_id=post_channel, photo=poster,
                caption=text, parse_mode="HTML", reply_markup=kb
            )
        else:
            await bot.send_message(
                chat_id=post_channel, text=text,
                parse_mode="HTML", reply_markup=kb
            )
        return True
    except Exception:
        try:
            await bot.send_message(
                chat_id=post_channel, text=text,
                parse_mode="HTML", reply_markup=kb
            )
            return True
        except Exception:
            return False


# ─── EXPORT USERS ────────────────────────────────────────────────────────────

async def _export_users(query, context):
    users = db.get_all_users_info(limit=10000)
    lines = ["ID,Username,Ism,Til,Ban,Sana"]
    for u in users:
        lines.append(f"{u['user_id']},{u['username']},{u['first_name']},{u['lang']},{u['is_banned']},{u['joined_at']}")
    csv_data = "\n".join(lines).encode("utf-8")
    buf = io.BytesIO(csv_data)
    buf.name = "users.csv"
    await context.bot.send_document(
        query.from_user.id,
        document=buf,
        filename="users.csv",
        caption=f"📥 Jami {len(users)} ta foydalanuvchi"
    )
