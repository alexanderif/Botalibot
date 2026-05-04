import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    Message, CallbackQuery
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = "8309349967:AAHONG8wJ69hjXuOc8XZ11vOpR9zL-UpsXg"
ADMIN_ID = 959173540

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class AdminStates(StatesGroup):
    waiting_card_number = State()
    waiting_card_info = State()
    waiting_price = State()
    waiting_service_title = State()
    waiting_broadcast = State()
    waiting_config_link = State()
    waiting_sub_link = State()
    waiting_support_id = State()


def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT,
            sub_link TEXT DEFAULT '',
            status TEXT DEFAULT 'free'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_id TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    try:
        c.execute("ALTER TABLE configs ADD COLUMN sub_link TEXT DEFAULT ''")
    except Exception:
        pass
    defaults = [
        ("card_number", "6037-9975-1234-5678"),
        ("card_info", "نام صاحب کارت"),
        ("service_price", "50000"),
        ("service_title", "سرویس یک ماهه"),
        ("support_id", ""),
    ]
    for key, val in defaults:
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
    conn.commit()
    conn.close()


def get_setting(key: str) -> str:
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""


def set_setting(key: str, value: str):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def get_user(user_id: int):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, balance FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row


def register_user(user_id: int):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id, balance) VALUES (?, 0)", (user_id,))
    conn.commit()
    conn.close()


def get_balance(user_id: int) -> int:
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0


def update_balance(user_id: int, amount: int):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def set_balance_db(user_id: int, amount: int):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance = ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def get_all_users():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, balance FROM users ORDER BY balance DESC")
    rows = c.fetchall()
    conn.close()
    return rows


def delete_user(user_id: int):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def save_payment(user_id: int, file_id: str) -> int:
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO payments (user_id, file_id, status) VALUES (?, ?, 'pending')", (user_id, file_id))
    payment_id = c.lastrowid
    conn.commit()
    conn.close()
    return payment_id


def update_payment_status(payment_id: int, status: str):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE payments SET status = ? WHERE id = ?", (status, payment_id))
    conn.commit()
    conn.close()


def get_payment(payment_id: int):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, user_id, file_id, status FROM payments WHERE id = ?", (payment_id,))
    row = c.fetchone()
    conn.close()
    return row


def get_pending_payments():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, user_id, status FROM payments WHERE status = 'pending'")
    rows = c.fetchall()
    conn.close()
    return rows


def get_free_config():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, link, sub_link FROM configs WHERE status = 'free' LIMIT 1")
    row = c.fetchone()
    conn.close()
    return row


def get_configs_by_status(status: str):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, link, sub_link, status FROM configs WHERE status = ? ORDER BY id DESC", (status,))
    rows = c.fetchall()
    conn.close()
    return rows


def mark_config_used(config_id: int):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE configs SET status = 'used' WHERE id = ?", (config_id,))
    conn.commit()
    conn.close()


def add_config_db(link: str, sub_link: str):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO configs (link, sub_link, status) VALUES (?, ?, 'free')", (link, sub_link))
    conn.commit()
    conn.close()


def delete_config(config_id: int) -> bool:
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM configs WHERE id = ?", (config_id,))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def get_stats():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM configs WHERE status = 'free'")
    free_configs = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM configs WHERE status = 'used'")
    used_configs = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending'")
    pending_payments = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM payments WHERE status = 'approved'")
    approved_payments = c.fetchone()[0]
    conn.close()
    return total_users, free_configs, used_configs, pending_payments, approved_payments


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def main_menu(user_id: int = 0):
    buttons = [
        [KeyboardButton(text="💰 افزایش موجودی"), KeyboardButton(text="📦 خرید سرویس")],
        [KeyboardButton(text="👤 حساب من"), KeyboardButton(text="🆘 پشتیبانی")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def admin_panel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 آمار کلی", callback_data="admin:stats"),
            InlineKeyboardButton(text="👥 کاربران", callback_data="admin:users"),
        ],
        [
            InlineKeyboardButton(text="🔗 مدیریت کانفیگ‌ها", callback_data="admin:configs_menu"),
            InlineKeyboardButton(text="💳 پرداخت‌های معلق", callback_data="admin:payments"),
        ],
        [
            InlineKeyboardButton(text="💵 تغییر تعرفه", callback_data="admin:change_price"),
            InlineKeyboardButton(text="🏦 تغییر کارت بانکی", callback_data="admin:change_card"),
        ],
        [
            InlineKeyboardButton(text="🆘 تنظیم پشتیبانی", callback_data="admin:set_support"),
            InlineKeyboardButton(text="📢 پیام همگانی", callback_data="admin:broadcast"),
        ],
    ])


def configs_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن کانفیگ جدید", callback_data="admin:add_config")],
        [InlineKeyboardButton(text="🟢 کانفیگ‌های موجود", callback_data="admin:configs_free")],
        [InlineKeyboardButton(text="🔴 کانفیگ‌های فروخته شده", callback_data="admin:configs_used")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:back")],
    ])


@dp.message(CommandStart())
async def cmd_start(message: Message):
    register_user(message.from_user.id)
    await message.answer(
        "سلام! 👋\nبه ربات خوش آمدید.\nیکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=main_menu(message.from_user.id)
    )


@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ شما دسترسی ندارید.")
        return
    await message.answer(
        "🛠 *پنل مدیریت*\n\nیکی از گزینه‌های زیر را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )


@dp.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    total_users, free_configs, used_configs, pending_payments, approved_payments = get_stats()
    price = get_setting("service_price")
    title = get_setting("service_title")
    card = get_setting("card_number")
    card_info = get_setting("card_info")
    await callback.message.edit_text(
        f"📊 *آمار کلی ربات*\n\n"
        f"👥 تعداد کاربران: *{total_users}*\n"
        f"🟢 کانفیگ‌های آزاد: *{free_configs}*\n"
        f"🔴 کانفیگ‌های فروخته شده: *{used_configs}*\n"
        f"⏳ پرداخت‌های معلق: *{pending_payments}*\n"
        f"💚 پرداخت‌های تأیید شده: *{approved_payments}*\n\n"
        f"📦 تعرفه: *{title}* — *{int(price):,}* تومان\n"
        f"🏦 کارت: `{card}`\n"
        f"👤 صاحب کارت: {card_info}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:back")]
        ])
    )
    await callback.answer()


@dp.callback_query(F.data == "admin:users")
async def admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    users = get_all_users()
    if not users:
        text = "👥 هیچ کاربری ثبت نشده است."
    else:
        lines = [f"👥 *لیست کاربران ({len(users)} نفر):*\n"]
        for uid, bal in users[:20]:
            lines.append(f"🆔 `{uid}` — موجودی: *{bal:,}* تومان")
        if len(users) > 20:
            lines.append(f"\n... و {len(users) - 20} کاربر دیگر")
        text = "\n".join(lines)
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:back")]
        ])
    )
    await callback.answer()


@dp.callback_query(F.data == "admin:configs_menu")
async def admin_configs_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    free_count = len(get_configs_by_status("free"))
    used_count = len(get_configs_by_status("used"))
    await callback.message.edit_text(
        f"🔗 *مدیریت کانفیگ‌ها*\n\n"
        f"🟢 موجود: *{free_count}* کانفیگ\n"
        f"🔴 فروخته شده: *{used_count}* کانفیگ",
        parse_mode="Markdown",
        reply_markup=configs_menu_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "admin:add_config")
async def admin_add_config_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    await callback.message.edit_text(
        "🔗 *افزودن کانفیگ جدید*\n\nلطفاً لینک کانفیگ را ارسال کنید:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ انصراف", callback_data="admin:configs_menu")]
        ])
    )
    await state.set_state(AdminStates.waiting_config_link)
    await callback.answer()


@dp.message(AdminStates.waiting_config_link)
async def process_config_link(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(config_link=message.text.strip())
    await message.answer(
        "✅ لینک کانفیگ ذخیره شد.\n\nحالا لینک سابسکریپشن را ارسال کنید:\n\n"
        "مثال:\n`http://193.5.44.32:2096/sub/a4a7pev2dgyhrdoo`",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_sub_link)


@dp.message(AdminStates.waiting_sub_link)
async def process_sub_link(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    config_link = data.get("config_link", "")
    sub_link = message.text.strip()
    add_config_db(config_link, sub_link)
    await message.answer(
        f"✅ *کانفیگ با موفقیت اضافه شد!*\n\n"
        f"🔗 لینک کانفیگ:\n`{config_link}`\n\n"
        f"📡 لینک ساب:\n`{sub_link}`",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )
    await state.clear()


@dp.callback_query(F.data == "admin:configs_free")
async def admin_configs_free(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    configs = get_configs_by_status("free")
    if not configs:
        text = "🟢 هیچ کانفیگ آزادی موجود نیست."
    else:
        lines = [f"🟢 *کانفیگ‌های موجود ({len(configs)} عدد):*\n"]
        for cid, link, sub, status in configs[:15]:
            short = link[:25] + "..." if len(link) > 25 else link
            lines.append(f"🆔 `{cid}` — `{short}`")
        if len(configs) > 15:
            lines.append(f"\n... و {len(configs) - 15} کانفیگ دیگر")
        text = "\n".join(lines)
    await callback.message.edit_text(
        text + "\n\n💡 برای حذف: `/delconfig <id>`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ افزودن کانفیگ", callback_data="admin:add_config")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:configs_menu")],
        ])
    )
    await callback.answer()


@dp.callback_query(F.data == "admin:configs_used")
async def admin_configs_used(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    configs = get_configs_by_status("used")
    if not configs:
        text = "🔴 هیچ کانفیگ فروخته شده‌ای وجود ندارد."
    else:
        lines = [f"🔴 *کانفیگ‌های فروخته شده ({len(configs)} عدد):*\n"]
        for cid, link, sub, status in configs[:15]:
            short = link[:25] + "..." if len(link) > 25 else link
            lines.append(f"🆔 `{cid}` — `{short}`")
        if len(configs) > 15:
            lines.append(f"\n... و {len(configs) - 15} کانفیگ دیگر")
        text = "\n".join(lines)
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:configs_menu")],
        ])
    )
    await callback.answer()


@dp.callback_query(F.data == "admin:payments")
async def admin_payments(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    payments = get_pending_payments()
    if not payments:
        text = "✅ هیچ پرداخت معلقی وجود ندارد."
    else:
        lines = [f"⏳ *پرداخت‌های معلق ({len(payments)} مورد):*\n"]
        for pid, uid, status in payments:
            lines.append(f"📋 شناسه: `{pid}` — کاربر: `{uid}`")
        text = "\n".join(lines)
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:back")]
        ])
    )
    await callback.answer()


@dp.callback_query(F.data == "admin:change_price")
async def admin_change_price(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    current_price = get_setting("service_price")
    current_title = get_setting("service_title")
    await callback.message.edit_text(
        f"💵 *تغییر تعرفه*\n\n"
        f"تعرفه فعلی: *{current_title}* — *{int(current_price):,}* تومان\n\n"
        f"لطفاً عنوان تعرفه را وارد کنید:\n"
        f"مثال: `1G یک ماهه`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ انصراف", callback_data="admin:back")]
        ])
    )
    await state.set_state(AdminStates.waiting_service_title)
    await callback.answer()


@dp.message(AdminStates.waiting_service_title)
async def process_service_title(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(service_title=message.text.strip())
    await message.answer(
        "✅ عنوان ذخیره شد.\n\nحالا *مبلغ* تعرفه را به تومان وارد کنید (فقط عدد):\nمثال: `170000`",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_price)


@dp.message(AdminStates.waiting_price)
async def process_new_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        new_price = int(message.text.strip().replace(",", ""))
        if new_price <= 0:
            raise ValueError
        data = await state.get_data()
        title = data.get("service_title", get_setting("service_title"))
        set_setting("service_price", str(new_price))
        set_setting("service_title", title)
        await message.answer(
            f"✅ تعرفه با موفقیت بروزرسانی شد:\n\n📦 *{title}* — *{new_price:,}* تومان",
            parse_mode="Markdown",
            reply_markup=admin_panel_keyboard()
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کنید.")


@dp.callback_query(F.data == "admin:change_card")
async def admin_change_card(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    current_card = get_setting("card_number")
    current_info = get_setting("card_info")
    await callback.message.edit_text(
        f"🏦 *تغییر کارت بانکی*\n\n"
        f"کارت فعلی: `{current_card}`\n"
        f"صاحب کارت: {current_info}\n\n"
        f"لطفاً شماره کارت جدید را وارد کنید:\nمثال: `6037-9975-1234-5678`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ انصراف", callback_data="admin:back")]
        ])
    )
    await state.set_state(AdminStates.waiting_card_number)
    await callback.answer()


@dp.message(AdminStates.waiting_card_number)
async def process_card_number(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(card_number=message.text.strip())
    await message.answer(
        "✅ شماره کارت ذخیره شد.\n\nحالا *نام صاحب کارت* را وارد کنید:\nمثال: `علی محمدی`",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_card_info)


@dp.message(AdminStates.waiting_card_info)
async def process_card_info(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    card_number = data.get("card_number", "")
    card_info = message.text.strip()
    set_setting("card_number", card_number)
    set_setting("card_info", card_info)
    await message.answer(
        f"✅ اطلاعات کارت بروزرسانی شد:\n\n🏦 `{card_number}`\n👤 {card_info}",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )
    await state.clear()


@dp.callback_query(F.data == "admin:set_support")
async def admin_set_support(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    current = get_setting("support_id")
    await callback.message.edit_text(
        f"🆘 *تنظیم پشتیبانی*\n\n"
        f"آیدی یا لینک فعلی: `{current or 'تنظیم نشده'}`\n\n"
        f"لطفاً یوزرنیم یا لینک پشتیبانی را وارد کنید:\nمثال: `@support_username`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ انصراف", callback_data="admin:back")]
        ])
    )
    await state.set_state(AdminStates.waiting_support_id)
    await callback.answer()


@dp.message(AdminStates.waiting_support_id)
async def process_support_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    support = message.text.strip()
    set_setting("support_id", support)
    await message.answer(
        f"✅ پشتیبانی به `{support}` تنظیم شد.",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )
    await state.clear()


@dp.callback_query(F.data == "admin:broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    await callback.message.edit_text(
        "📢 پیام همگانی خود را بنویسید:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ انصراف", callback_data="admin:back")]
        ])
    )
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.answer()


@dp.message(AdminStates.waiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    users = get_all_users()
    sent = 0
    failed = 0
    for uid, _ in users:
        try:
            await bot.send_message(uid, f"📢 *پیام مدیریت:*\n\n{message.text}", parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1
    await message.answer(
        f"📢 ارسال پیام همگانی تمام شد.\n✅ موفق: *{sent}*\n❌ ناموفق: *{failed}*",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )
    await state.clear()


@dp.callback_query(F.data == "admin:back")
async def admin_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🛠 *پنل مدیریت*\n\nیکی از گزینه‌های زیر را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )
    await callback.answer()


@dp.message(Command("delconfig"))
async def del_config_cmd(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ شما دسترسی ندارید.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ استفاده صحیح:\n`/delconfig <id>`", parse_mode="Markdown")
        return
    try:
        config_id = int(parts[1].strip())
        success = delete_config(config_id)
        if success:
            await message.answer(f"✅ کانفیگ شماره `{config_id}` حذف شد.", parse_mode="Markdown")
        else:
            await message.answer(f"❌ کانفیگ با شناسه `{config_id}` پیدا نشد.", parse_mode="Markdown")
    except ValueError:
        await message.answer("❌ شناسه باید عدد باشد.")


@dp.message(Command("setbalance"))
async def set_balance_cmd(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ شما دسترسی ندارید.")
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ استفاده صحیح:\n`/setbalance <user_id> <مقدار>`", parse_mode="Markdown")
        return
    try:
        uid = int(parts[1])
        amount = int(parts[2])
        user = get_user(uid)
        if not user:
            await message.answer("❌ کاربر پیدا نشد.")
            return
        set_balance_db(uid, amount)
        await message.answer(f"✅ موجودی کاربر `{uid}` به *{amount:,}* تومان تنظیم شد.", parse_mode="Markdown")
        await bot.send_message(uid, f"💰 موجودی شما توسط مدیریت به *{amount:,}* تومان تنظیم شد.", parse_mode="Markdown")
    except ValueError:
        await message.answer("❌ مقادیر وارد شده معتبر نیستند.")


@dp.message(Command("addbalance"))
async def add_balance_cmd(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ شما دسترسی ندارید.")
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ استفاده صحیح:\n`/addbalance <user_id> <مقدار>`", parse_mode="Markdown")
        return
    try:
        uid = int(parts[1])
        amount = int(parts[2])
        user = get_user(uid)
        if not user:
            await message.answer("❌ کاربر پیدا نشد.")
            return
        update_balance(uid, amount)
        new_bal = get_balance(uid)
        await message.answer(f"✅ *{amount:,}* تومان به کاربر `{uid}` افزوده شد.\nموجودی جدید: *{new_bal:,}* تومان", parse_mode="Markdown")
        await bot.send_message(uid, f"💰 مبلغ *{amount:,}* تومان توسط مدیریت به موجودی شما افزوده شد.", parse_mode="Markdown")
    except ValueError:
        await message.answer("❌ مقادیر وارد شده معتبر نیستند.")


@dp.message(Command("deleteuser"))
async def delete_user_cmd(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ شما دسترسی ندارید.")
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ استفاده صحیح:\n`/deleteuser <user_id>`", parse_mode="Markdown")
        return
    try:
        uid = int(parts[1])
        delete_user(uid)
        await message.answer(f"✅ کاربر `{uid}` از پایگاه داده حذف شد.", parse_mode="Markdown")
    except ValueError:
        await message.answer("❌ شناسه باید عدد باشد.")


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ شما دسترسی ندارید.")
        return
    total_users, free_configs, used_configs, pending_payments, approved_payments = get_stats()
    price = get_setting("service_price")
    title = get_setting("service_title")
    await message.answer(
        f"📊 *آمار کلی ربات*\n\n"
        f"👥 کاربران: *{total_users}*\n"
        f"🟢 کانفیگ آزاد: *{free_configs}*\n"
        f"🔴 کانفیگ فروخته شده: *{used_configs}*\n"
        f"⏳ پرداخت معلق: *{pending_payments}*\n"
        f"💚 پرداخت تأیید شده: *{approved_payments}*\n"
        f"💵 تعرفه: *{title}* — *{int(price):,}* تومان",
        parse_mode="Markdown"
    )


@dp.message(F.text == "👤 حساب من")
async def my_account(message: Message):
    register_user(message.from_user.id)
    balance = get_balance(message.from_user.id)
    await message.answer(
        f"👤 *حساب کاربری*\n\n"
        f"🆔 شناسه شما: `{message.from_user.id}`\n"
        f"💰 موجودی: *{balance:,}* تومان",
        parse_mode="Markdown"
    )


@dp.message(F.text == "🆘 پشتیبانی")
async def support_handler(message: Message):
    support = get_setting("support_id")
    if not support:
        await message.answer("❌ پشتیبانی در حال حاضر در دسترس نیست.\nلطفاً بعداً تلاش کنید.")
    else:
        await message.answer(
            f"🆘 *پشتیبانی*\n\nبرای ارتباط با پشتیبانی:\n👤 {support}",
            parse_mode="Markdown"
        )


@dp.message(F.text == "💰 افزایش موجودی")
async def increase_balance(message: Message):
    register_user(message.from_user.id)
    card = get_setting("card_number")
    card_info = get_setting("card_info")
    price = get_setting("service_price")
    title = get_setting("service_title")
    await message.answer(
        f"💳 *افزایش موجودی*\n\n"
        f"📦 تعرفه: *{title}* — *{int(price):,}* تومان\n\n"
        f"مبلغ دلخواه را به کارت زیر واریز کنید:\n\n"
        f"`{card}`\n"
        f"👤 {card_info}\n\n"
        f"پس از واریز، تصویر رسید پرداخت را ارسال کنید.",
        parse_mode="Markdown"
    )


@dp.message(F.photo)
async def handle_photo(message: Message):
    register_user(message.from_user.id)
    file_id = message.photo[-1].file_id
    payment_id = save_payment(message.from_user.id, file_id)

    approve_btn = InlineKeyboardButton(text="تأیید ✅", callback_data=f"approve:{payment_id}")
    reject_btn = InlineKeyboardButton(text="رد ❌", callback_data=f"reject:{payment_id}")
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[[approve_btn, reject_btn]])

    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=file_id,
        caption=f"📥 *درخواست افزایش موجودی*\n\n"
                f"👤 کاربر: `{message.from_user.id}`\n"
                f"🔖 شناسه پرداخت: `{payment_id}`",
        parse_mode="Markdown",
        reply_markup=inline_kb
    )
    await message.answer("✅ رسید شما دریافت شد و در انتظار تأیید ادمین است.")


@dp.callback_query(F.data.startswith("approve:"))
async def approve_payment(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ شما دسترسی ندارید.", show_alert=True)
        return
    payment_id = int(callback.data.split(":")[1])
    payment = get_payment(payment_id)
    if not payment:
        await callback.answer("پرداخت یافت نشد.", show_alert=True)
        return
    if payment[3] != "pending":
        await callback.answer("این پرداخت قبلاً پردازش شده است.", show_alert=True)
        return
    user_id = payment[1]
    reward = int(get_setting("service_price"))
    update_balance(user_id, reward)
    update_payment_status(payment_id, "approved")
    await bot.send_message(
        chat_id=user_id,
        text=f"✅ پرداخت شما تأیید شد!\n💰 مبلغ *{reward:,}* تومان به موجودی شما افزوده شد.",
        parse_mode="Markdown"
    )
    await callback.answer("پرداخت تأیید شد ✅")
    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n✅ *تأیید شد*",
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("reject:"))
async def reject_payment(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ شما دسترسی ندارید.", show_alert=True)
        return
    payment_id = int(callback.data.split(":")[1])
    payment = get_payment(payment_id)
    if not payment:
        await callback.answer("پرداخت یافت نشد.", show_alert=True)
        return
    if payment[3] != "pending":
        await callback.answer("این پرداخت قبلاً پردازش شده است.", show_alert=True)
        return
    user_id = payment[1]
    update_payment_status(payment_id, "rejected")
    await bot.send_message(
        chat_id=user_id,
        text="❌ متأسفانه پرداخت شما تأیید نشد.\nلطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
    )
    await callback.answer("پرداخت رد شد ❌")
    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n❌ *رد شد*",
        parse_mode="Markdown"
    )


@dp.message(F.text == "📦 خرید سرویس")
async def buy_service(message: Message):
    register_user(message.from_user.id)
    balance = get_balance(message.from_user.id)
    price = int(get_setting("service_price"))
    title = get_setting("service_title")
    if balance < price:
        await message.answer(
            f"❌ موجودی شما کافی نیست.\n\n"
            f"📦 سرویس: *{title}*\n"
            f"💵 هزینه: *{price:,}* تومان\n"
            f"💰 موجودی شما: *{balance:,}* تومان\n\n"
            f"لطفاً ابتدا موجودی خود را افزایش دهید.",
            parse_mode="Markdown"
        )
        return
    config = get_free_config()
    if not config:
        await message.answer("❌ در حال حاضر سرویسی موجود نیست.\nلطفاً بعداً دوباره تلاش کنید.")
        return
    config_id, config_link, sub_link = config
    mark_config_used(config_id)
    update_balance(message.from_user.id, -price)
    new_balance = balance - price

    text = (
        f"✅ *خرید موفق!*\n\n"
        f"📦 سرویس: *{title}*\n\n"
        f"🔗 لینک کانفیگ:\n`{config_link}`\n\n"
    )
    if sub_link:
        text += f"📡 لینک سابسکریپشن:\n`{sub_link}`\n\n"
    text += f"💰 موجودی باقیمانده: *{new_balance:,}* تومان"

    await message.answer(text, parse_mode="Markdown")


async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
