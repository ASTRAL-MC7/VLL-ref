import asyncio

from aiogram import Router, F
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter, TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from config import ADMIN_IDS
from keyboards import admin_menu_kb

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class RefMessageState(StatesGroup):
    waiting_for_content = State()


class BroadcastState(StatesGroup):
    waiting_for_content = State()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🛠 Admin panel", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin_users_count")
async def cb_users_count(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    total = await db.count_users()
    await callback.answer(f"👥 Foydalanuvchilar soni: {total}", show_alert=True)


@router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    top = await db.get_top(10)
    if not top:
        text = "Hozircha ma'lumot yo'q."
    else:
        lines = ["📊 <b>TOP 10 referal</b>\n"]
        for i, row in enumerate(top, start=1):
            name = row["first_name"] or (f"@{row['username']}" if row["username"] else str(row["user_id"]))
            lines.append(f"{i}. {name} — {row['ref_count']} ta (ID: {row['user_id']})")
        text = "\n".join(lines)
    await callback.message.answer(text)
    await callback.answer()


@router.message(Command("addref"))
async def cmd_addref(message: Message, command_args: str | None = None):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Foydalanish: /addref <user_id> <amount>")
        return
    try:
        target_id, amount = int(parts[1]), int(parts[2])
    except ValueError:
        await message.answer("user_id va amount butun son bo'lishi kerak.")
        return
    await db.add_ref_count(target_id, amount)
    await message.answer(f"✅ {target_id} ga {amount} ta referal qo'shildi.")


@router.message(Command("delref"))
async def cmd_delref(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Foydalanish: /delref <user_id> <amount>")
        return
    try:
        target_id, amount = int(parts[1]), int(parts[2])
    except ValueError:
        await message.answer("user_id va amount butun son bo'lishi kerak.")
        return
    await db.add_ref_count(target_id, -amount)
    await message.answer(f"✅ {target_id} dan {amount} ta referal ayirildi.")


@router.message(Command("refmessage"))
async def cmd_refmessage(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(RefMessageState.waiting_for_content)
    await message.answer(
        "Yangi referal xabarini yuboring.\n\n"
        "Bu matn, rasm yoki rasm + izoh (caption) bo'lishi mumkin.\n"
        "Botga yuborilgan xabar oxiriga foydalanuvchining shaxsiy havolasi "
        "avtomatik qo'shiladi."
    )


@router.message(RefMessageState.waiting_for_content, F.photo)
async def save_refmessage_photo(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    caption = message.caption or ""
    await db.set_ref_message("photo", file_id, caption)
    await state.clear()
    await message.answer("✅ Referal xabari (rasm) saqlandi.")


@router.message(RefMessageState.waiting_for_content, F.text)
async def save_refmessage_text(message: Message, state: FSMContext):
    await db.set_ref_message("text", None, message.text)
    await state.clear()
    await message.answer("✅ Referal xabari (matn) saqlandi.")


@router.message(Command("xabar"))
async def cmd_xabar(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(BroadcastState.waiting_for_content)
    await message.answer(
        "Barchaga yuboriladigan xabarni jo'nating.\n\n"
        "Matn, rasm, video yoki boshqa istalgan turdagi xabar bo'lishi mumkin — "
        "u qanday yuborilsa, hammaga xuddi shunday yetkaziladi."
    )


@router.message(BroadcastState.waiting_for_content)
async def do_broadcast(message: Message, state: FSMContext):
    await state.clear()

    async with db.pool().acquire() as conn:
        rows = await conn.fetch("SELECT user_id FROM users WHERE is_verified=TRUE")
    user_ids = [row["user_id"] for row in rows]

    status = await message.answer(f"⏳ Yuborilmoqda... (0/{len(user_ids)})")
    sent, failed = 0, 0

    for i, user_id in enumerate(user_ids, start=1):
        try:
            await message.copy_to(user_id)
            sent += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await message.copy_to(user_id)
                sent += 1
            except (TelegramForbiddenError, TelegramBadRequest):
                failed += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1  # user blocked the bot / deleted account / etc.

        if i % 25 == 0:
            await status.edit_text(f"⏳ Yuborilmoqda... ({i}/{len(user_ids)})")
        await asyncio.sleep(0.05)  # stay under Telegram's rate limits

    await status.edit_text(
        f"✅ Xabar yuborildi.\nMuvaffaqiyatli: {sent}\nXato (bloklangan/o'chirilgan): {failed}"
    )
