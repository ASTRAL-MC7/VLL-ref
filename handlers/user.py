from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

import database as db
from config import CHANNELS, BOT_USERNAME, PRIZES
from keyboards import channels_kb, main_menu_kb, back_to_menu_kb

router = Router()

OK_STATUSES = {"member", "administrator", "creator"}


async def user_joined_all_channels(bot: Bot, user_id: int) -> bool:
    for ch in CHANNELS:
        target = ch["chat_id"] if ch["chat_id"] else f"@{ch['username']}"
        if not target:
            continue
        try:
            member = await bot.get_chat_member(target, user_id)
            if member.status not in OK_STATUSES:
                return False
        except TelegramBadRequest:
            # bot can't see membership (not admin there, wrong id, etc.) -> fail closed
            return False
    return True


def reflink(user_id: int) -> str:
    return f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    user_id = message.from_user.id

    # capture referral payload, e.g. /start ref_123456
    if command.args and command.args.startswith("ref_"):
        try:
            referrer_id = int(command.args.removeprefix("ref_"))
            await db.stash_pending_referral(user_id, referrer_id)
        except ValueError:
            pass

    if await db.is_verified(user_id):
        await message.answer(
            "Salom! Asosiy menyu 👇",
            reply_markup=main_menu_kb(),
        )
        return

    await message.answer(
        "Assalomu alaykum! 👋\n\n"
        "Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling, "
        "so'ng <b>✅ Tekshirish</b> tugmasini bosing.",
        reply_markup=channels_kb(),
    )


@router.callback_query(F.data == "check_sub")
async def cb_check_sub(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    if not await user_joined_all_channels(bot, user_id):
        await callback.answer(
            "❌ Siz hali barcha kanallarga a'zo bo'lmadingiz!", show_alert=True
        )
        return

    is_first_time = await db.register_and_verify(
        user_id,
        callback.from_user.username or "",
        callback.from_user.first_name or "",
    )

    if is_first_time:
        referrer_id = await db.get_referrer_id(user_id)
        if referrer_id:
            try:
                await bot.send_message(
                    referrer_id,
                    "🎉 Sizning taklif havolangiz orqali yangi foydalanuvchi qo'shildi! "
                    "+1 referal, +1 Vcoin",
                )
            except TelegramBadRequest:
                pass

    await callback.message.edit_text("✅ A'zolik tasdiqlandi! Asosiy menyu 👇")
    await callback.message.answer("Asosiy menyu:", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text("Asosiy menyu:", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "my_balance")
async def cb_my_balance(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    vcoin = user["vcoin"] if user else 0
    ref_count = user["ref_count"] if user else 0
    await callback.message.edit_text(
        f"💰 Balansingiz: <b>{vcoin} Vcoin</b>\n"
        f"🤝 Takliflaringiz: <b>{ref_count} ta</b>",
        reply_markup=back_to_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "my_link")
async def cb_my_link(callback: CallbackQuery):
    user_id = callback.from_user.id
    link = reflink(user_id)
    template = await db.get_ref_message()

    if template and template["content_type"] == "photo":
        caption = (template["text_content"] or "") + f"\n\n{link}"
        await callback.message.answer_photo(photo=template["file_id"], caption=caption)
    elif template and template["content_type"] == "text":
        text = (template["text_content"] or "") + f"\n\n{link}"
        await callback.message.answer(text)
    else:
        await callback.message.answer(
            "🔗 Sizning taklif havolangiz:\n\n"
            f"{link}\n\n"
            "Do'stlaringizni taklif qiling va Vcoin va sovg'alar yutib oling!"
        )
    await callback.answer()


@router.callback_query(F.data == "stats")
async def cb_stats(callback: CallbackQuery):
    top = await db.get_top(3)
    medals = ["🥇", "🥈", "🥉"]
    lines = ["📊 <b>TOP 3 ishtirokchi</b>\n"]
    if not top:
        lines.append("Hozircha statistika mavjud emas.")
    for i, row in enumerate(top):
        name = row["first_name"] or (f"@{row['username']}" if row["username"] else "Foydalanuvchi")
        lines.append(f"{medals[i]} {name} - {row['ref_count']} ta")

    rank, ref_count = await db.get_rank(callback.from_user.id)
    lines.append("")
    if rank:
        lines.append(f"#{rank} - o'rin  siz ({ref_count} ta)")
    else:
        lines.append("Siz hali ro'yxatdan o'tmagansiz.")

    await callback.message.edit_text("\n".join(lines), reply_markup=back_to_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "prizes")
async def cb_prizes(callback: CallbackQuery):
    lines = ["🏆 <b>Sovg'alar</b> (referal soni bo'yicha)\n"]
    for place, prize in PRIZES:
        lines.append(f"{place} — {prize}")
    await callback.message.edit_text("\n".join(lines), reply_markup=back_to_menu_kb())
    await callback.answer()
