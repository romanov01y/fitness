import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from google import genai
from google.genai import types as genai_types
from config import BOT_TOKEN

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализируем клиента Gemini (автоматически подтягивает GEMINI_API_KEY)
gemini_client = genai.Client()

# Глобальная системная инструкция для роли тренера
SYSTEM_INSTRUCTION = (
    "Ты — квалифицированный, дружелюбный и мотивирующий личный фитнес-тренер "
    "и нутрициолог. Отвечай на вопросы пользователя развернуто, профессионально, "
    "давай практические советы по тренировкам и питанию."
)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я твой персональный ИИ-тренер на базе Gemini.\n\n"
        "Ты можешь общаться со мной на любые темы: задавай вопросы про упражнения, "
        "проси составить план питания, рецепты или программу тренировок."
    )

# 🤖 ГЛАВНЫЙ ОБРАБОТЧИК: Прямой запрос к Gemini
@dp.message(F.text)
async def chat_with_gemini(message: types.Message):
    # Включаем статус "печатает..." в Telegram
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # Используем самый надежный метод generate_content напрямую.
        # Передаем роль тренера через системную инструкцию в конфигурации.
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=message.text,
            config=genai_types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7
            )
        )
        
        # Отправляем ответ пользователю в красивом Markdown-формате
        await message.answer(response.text, parse_mode="Markdown")
        
    except Exception as e:
        print(f"Ошибка при запросе к Gemini: {e}")
        await message.answer("⚠️ Извини, произошла ошибка при обработке запроса. Попробуй еще раз.")


# --- ФЕЙКОВЫЙ СЕРВЕР ДЛЯ ОБМАНА RENDER ---
async def handle_ping(reader, writer):
    await reader.read(1024)
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        "Content-Length: 2\r\n"
        "Connection: close\r\n"
        "\r\n"
        "OK"
    )
    writer.write(response.encode('utf-8'))
    await writer.drain()
    writer.close()
    await writer.wait_closed()

async def start_dummy_server():
    port = int(os.environ.get("PORT", 8000))
    server = await asyncio.start_server(handle_ping, '0.0.0.0', port)
    print(f"Фейковый веб-сервер запущен на порту {port}")
    async with server:
        await server.serve_forever()


async def main():
    # Запускаем фоновый веб-сервер для прохождения проверок Render
    asyncio.create_task(start_dummy_server())
    
    # Очищаем очередь старых сообщений, чтобы не ловить конфликты
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем поллинг бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
