import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite

TOKEN = "8559139266:AAGNH98-yG7ONb2XGRizntz_WOS7OJInL5Q"
ADMIN_ID = 2102514325
CHANNEL = "@dpui1"

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ---------------- DB ----------------
async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            ref INTEGER,
            balance INTEGER DEFAULT 0
        )
        """)
        await db.commit()


# ---------------- CHECK SUB ----------------
async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# ---------------- START ----------------
@dp.message(F.text.startswith("/start"))
async def start(message: Message):
    user_id = message.from_user.id
    ref = message.text.split(" ")[1] if len(message.text.split(" ")) > 1 else None

    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = await cur.fetchone()

        if not user:
            await db.execute("INSERT INTO users(user_id, ref) VALUES(?,?)", (user_id, ref))
            if ref:
                await db.execute("UPDATE users SET balance = balance + 1000 WHERE user_id=?", (ref,))
            await db.commit()

    if not await is_subscribed(user_id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo‘lish", url=f"https://t.me/{CHANNEL[1:]}")],
            [InlineKeyboardButton(text="♻ Tekshirish", callback_data="check")]
        ])
        return await message.answer("Botdan foydalanish uchun kanalga obuna bo‘ling!", reply_markup=kb)

    await message.answer("👋 Xush kelibsiz!\nReferral link:\n/t.me/yourbot?start={user_id}")


# ---------------- SIGNAL (ADMIN) ----------------
@dp.message(F.text.startswith("/signal"))
async def signal(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.replace("/signal", "").strip()

    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute("SELECT user_id FROM users")
        users = await cur.fetchall()

    for u in users:
        try:
            await bot.send_message(u[0], f"📊 SIGNAL:\n{text}")
        except:
            pass

    await message.answer("Signal yuborildi")


# ---------------- BALANCE ----------------
@dp.message(F.text == "/balance")
async def balance(message: Message):
    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
        bal = await cur.fetchone()

    await message.answer(f"💰 Balans: {bal[0] if bal else 0}")


# ---------------- CALLBACK CHECK ----------------
@dp.callback_query(F.data == "check")
async def check(call):
    if await is_subscribed(call.from_user.id):
        await call.message.edit_text("✅ Tasdiqlandi! Botdan foydalanishingiz mumkin.")
    else:
        await call.answer("Hali obuna bo‘lmadingiz!", show_alert=True)


# ---------------- RUN ----------------
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
