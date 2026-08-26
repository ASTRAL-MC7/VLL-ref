from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CHANNELS


def channels_kb() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"📢 {c['title']}", url=c["url"])] for c in CHANNELS]
    rows.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_menu_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="💰 Mening balim", callback_data="my_balance")],
        [InlineKeyboardButton(text="🔗 Mening linkim", callback_data="my_link")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="stats")],
        [InlineKeyboardButton(text="🏆 Sovg'alar", callback_data="prizes")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_menu")]]
    )


def admin_menu_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="👥 Users count", callback_data="admin_users_count")],
        [InlineKeyboardButton(text="📊 Stats (top 10)", callback_data="admin_stats")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
