import asyncio
import logging
import sys
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
# from motor.motor_asyncio import AsyncIOMotorClient # MongoDB uchun

# Bot tokenini shu yerga kiritamiz
BOT_TOKEN = "8989105948:AAFDxVlLMSdfwDHFPlODP81fFkvFJ9QBHjY"
# MONGO_URI = os.getenv("MONGO_URI", "Sizning_MongoDB_Havolangiz")
PORT = int(os.getenv("PORT", 8080))

# Dispatcher yaratamiz
dp = Dispatcher()

# Admin ID si (Hozircha 0 qilib turamiz, o'zingiznikini bilib olishingiz uchun)
ADMIN_ID = 6756534512

# Botning o'ziga yozganda ishlaydigan funksiya (Murojaat boti)
@dp.message()
async def direct_message_handler(message: Message) -> None:
    # Agar admin ID hali kiritilmagan bo'lsa, foydalanuvchiga ID sini ko'rsatamiz
    if ADMIN_ID == 0:
        await message.answer(f"Sizning Telegram ID raqamingiz: `{message.from_user.id}`\n\nIltimos, shu raqamni nusxalab menga (dasturchiga) yuboring. Keyin men uni kodga kiritaman va bot to'liq ishga tushadi.")
        return

    # Agar xabar yozgan odam admin bo'lmasa, uni adminga yetkazamiz
    if message.from_user.id != ADMIN_ID:
        try:
            await message.forward(chat_id=ADMIN_ID)
            await message.answer("✅ Xabaringiz adminga yuborildi. Tez orada javob qaytaramiz!")
        except Exception as e:
            await message.answer("Xabar yuborishda xatolik yuz berdi.")
            logging.error(f"Forward xatoligi: {e}")
    else:
        # Agar admin botga yozsa va birovning xabariga (Reply qilib) javob berayotgan bo'lsa
        if message.reply_to_message and message.reply_to_message.forward_origin:
            origin = message.reply_to_message.forward_origin
            if origin.type == 'user':
                user_id = origin.sender_user.id
                try:
                    await message.copy_to(chat_id=user_id)
                except Exception as e:
                    await message.answer(f"Foydalanuvchiga xabar borishida xatolik: {e}")
            else:
                await message.answer("Bu foydalanuvchining profili yashiringanligi sababli bot unga bevosita javob yoza olmaydi.")
        else:
            await message.answer("Mijozga javob yozish uchun uning yuborgan xabariga 'Reply' (Javob berish) tugmasini bosib yozing.")

# Telegram Business orqali shaxsiy akkauntga kelgan xabarlarga javob berish
@dp.business_message()
async def business_message_handler(message: Message) -> None:
    # Bu yerda sizning shaxsiy lichkangizga yozgan odamga yuboriladigan avtomatik xabar
    auto_reply_text = (
        "Assalomu alaykum! Men hozir bandman yoki offlineman xabaringizni ko'rishim bilan javob qaytaraman. 🙂\n\n"
        "_(Hurmat bilan avto javob bergich)_"
    )
    
    try:
        # Xabarga javob qaytarish
        await message.answer(auto_reply_text)
        logging.info(f"Yangi xabarga avto-javob yuborildi. Kimdan: {message.from_user.full_name}")
    except Exception as e:
        logging.error(f"Xabar yuborishda xatolik yuz berdi: {e}")

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
    # MongoDB ga ulanish (havola bo'lganda yoqamiz)
    # client = AsyncIOMotorClient(MONGO_URI)
    # db = client.bot_database
    # print("MongoDB ga ulandi!")
    
    # Botni ishga tushirish
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
