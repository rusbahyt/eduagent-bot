import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Қате: TELEGRAM_BOT_TOKEN немесе GEMINI_API_KEY табылмады!")

genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel("gemini-1.5-flash")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

TEMP_DIR = "temp_images"
os.makedirs(TEMP_DIR, exist_ok=True)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        f"Сәлеметсіз бе, {message.from_user.first_name}!\n"
        "🤖 **EduAgent AI** ботына қош келдіңіз.\n\n"
        "Маған кез келген сұрақ қойыңыз немесе қолжазба есептің/тапсырманың суретін жіберіңіз — мен оны оқып, талдап, көмектесемін!"
    )

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    local_image_path = None
    
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_path = file_info.file_path

        local_image_path = os.path.join(TEMP_DIR, f"{photo.file_id}.jpg")
        await bot.download_file(file_path, local_image_path)

        sample_file = genai.upload_file(path=local_image_path, display_name="Student Submission")
        prompt = message.caption if message.caption else "Бұл суретте не көрсетілген? Қолжазба мәтінді немесе есепті оқып, толық талдау жасап бер."

        response = ai_model.generate_content([sample_file, prompt])
        await message.answer(response.text)

    except Exception as e:
        logging.error(f"Суретті өңдеу қатесі: {e}")
        await message.answer("Кешіріңіз, суретті өңдеу кезінде қате орын алды.")
    
    finally:
        if local_image_path and os.path.exists(local_image_path):
            os.remove(local_image_path)

@dp.message(F.text)
async def text_handler(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    try:
        response = ai_model.generate_content(message.text)
        await message.answer(response.text)
    except Exception as e:
        logging.error(f"Мәтінді өңдеу қатесі: {e}")
        await message.answer("Кешіріңіз, сұранысты өңдеу кезінде қате шықты.")

async def main():
    print("EduAgent AI Телеграм боты сәтті іске қосылды...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())