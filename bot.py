import asyncio
import logging
import sys
import os
import json
import re
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart

# Bot tokenini shu yerga kiritamiz
BOT_TOKEN = "8989105948:AAFDxVlLMSdfwDHFPlODP81fFkvFJ9QBHjY"
PORT = int(os.getenv("PORT", 8080))

# Dispatcher yaratamiz
dp = Dispatcher()

# Admin ID si
ADMIN_ID = 6756534512
USERS_FILE = "users_db.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user(user_id, phone):
    users = load_users()
    users[str(user_id)] = phone
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def get_user_phone(user_id):
    users = load_users()
    return users.get(str(user_id))

# START buyrug'i
@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if message.from_user.id == ADMIN_ID:
        await message.answer("Assalomu alaykum Admin! Men sizga kelgan xabarlarni yetkazishga tayyorman.")
        return

    phone = get_user_phone(message.from_user.id)
    if not phone:
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
            resize_keyboard=True
        )
        await message.answer("Assalomu alaykum! Murojaat yo'llash uchun iltimos, pastdagi tugmani bosish orqali telefon raqamingizni tasdiqlang:", reply_markup=kb)
    else:
        await message.answer("Siz ro'yxatdan o'tgansiz. Bemalol murojaatingizni (matn, rasm, video, fayl, ovozli xabar) yuborishingiz mumkin.")

# Raqamni qabul qilish
@dp.message(F.contact)
async def handle_contact(message: Message) -> None:
    if message.contact:
        save_user(message.from_user.id, message.contact.phone_number)
        await message.answer("Rahmat! Raqamingiz qabul qilindi. Endi bemalol xabar, rasm, video yoki fayllarni menga yuboring, barchasini adminga yetkazaman.", reply_markup=ReplyKeyboardRemove())

# Telegram Business orqali shaxsiy akkauntga kelgan xabarlarga javob berish
@dp.business_message()
async def business_message_handler(message: Message) -> None:
    # Bu yerda sizning shaxsiy lichkangizga yozgan odamga yuboriladigan avtomatik xabar
    auto_reply_text = (
        "Assalomu alaykum! Men hozir bandman yoki offlineman xabaringizni ko'rishim bilan javob qaytaraman. 🙂\n\n"
        "_(Hurmat bilan avto javob bergich)_"
    )
    
    try:
        await message.answer(auto_reply_text)
        logging.info(f"Yangi xabarga avto-javob yuborildi. Kimdan: {message.from_user.full_name}")
    except Exception as e:
        logging.error(f"Xabar yuborishda xatolik yuz berdi: {e}")

# Murojaat boti logikasi (rasm, video, fayl, text)
@dp.message()
async def direct_message_handler(message: Message, bot: Bot) -> None:
    if message.from_user.id != ADMIN_ID:
        # Foydalanuvchi adminga yozyapti
        phone = get_user_phone(message.from_user.id)
        if not phone:
            kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
                resize_keyboard=True
            )
            await message.answer("Xabar yuborishdan oldin, iltimos telefon raqamingizni yuboring:", reply_markup=kb)
            return

        try:
            # Xabarni adminga copy_to yordamida uzatish (rasm/video farqi yo'q)
            fw = await message.copy_to(chat_id=ADMIN_ID)
            
            # Mijoz ma'lumotlari bilan xabar
            username = f"@{message.from_user.username}" if message.from_user.username else "yo'q"
            info_text = (
                f"👤 Ism: {message.from_user.full_name}\n"
                f"🌐 Username: {username}\n"
                f"🆔 ID: {message.from_user.id}\n"
                f"📱 Tel: {phone}\n\n"
                f"⬇️ Javob yozish uchun SHU xabarga 'Reply' qiling."
            )
            await bot.send_message(chat_id=ADMIN_ID, text=info_text, reply_to_message_id=fw.message_id)
            await message.answer("✅ Xabaringiz adminga yetkazildi!")
        except Exception as e:
            await message.answer("Xabar yuborishda xatolik yuz berdi.")
            logging.error(f"Forward xatoligi: {e}")
    else:
        # Admin mijozga javob yozyapti
        if message.reply_to_message:
            replied_text = message.reply_to_message.text or ""
            
            # Agar admin yuborilgan ma'lumot xabariga reply qilsa, ID ni qidiramiz
            match = re.search(r"🆔 ID: (\d+)", replied_text)
            if match:
                user_id = match.group(1)
                try:
                    await message.copy_to(chat_id=int(user_id))
                except Exception as e:
                    await message.answer(f"Foydalanuvchiga xabar borishida xatolik: {e}")
            else:
                await message.answer("Iltimos, javob yozish uchun ichida 'ID' si yozilgan ma'lumotnoma xabariga 'Reply' qiling.")
        else:
            await message.answer("Mijozga javob yozish uchun ma'lumot xabariga 'Reply' (Javob berish) tugmasini bosib yozing.")

# Render uchun oddiy Web Server
async def handle_ping(request):
    return web.Response(text="Bot ishlayapti!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logging.info(f"Web server port {PORT} da ishga tushdi.")

async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    logging.info("Telegram Business boti ishga tushmoqda...")
    
    # Web server va botni birga ishga tushirish
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
