import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from google import genai
from config import BOT_TOKEN

# Инициализация бота и диспетчера aiogram
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализируем клиента Gemini (код автоматически возьмет переменную GEMINI_API_KEY)
gemini_client = genai.Client()

# Создаем сессию чата с системной инструкцией.
# Здесь задается роль нейросети — ты можешь изменить текст под свои задачи.
gemini_chat = gemini_client.chats.create(
    model="gemini-1.5-flash",
    config={
        "system_instruction": (
            "Ты — квалифицированный, дружелюбный и мотивирующий личный фитнес-тренер "
            "и нутрициолог. Отвечай на вопросы пользователя развернуто, профессионально, "
            "давай практические советы по тренировкам и питанию."
        )
    }
)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я твой персональный ИИ-тренер на базе Gemini.\n\n"
        "Ты можешь общаться со мной на любые темы: задавай вопросы про упражнения, "
        "проси составить план питания, рецепты или программу тренировок. "
        "Я помню контекст нашего разговора, так что мы можем вести полноценный диалог!"
    )

# 🤖 ГЛАВНЫЙ ОБРАБОТЧИК: Отправка сообщений в Gemini
@dp.message(F.text)
async def chat_with_gemini(message: types.Message):
    # Показываем статус "печатает...", пока нейросеть формирует ответ
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # Отправляем текст пользователя в чат-сессию Gemini
        response = gemini_chat.send_message(message.text)
        
        # Отправляем ответ нейросети обратно пользователю в Telegram
        # parse_mode="Markdown" позволяет Gemini красиво форматировать списки и жирный текст
        await message.answer(response.text, parse_mode="Markdown")
        
    except Exception as e:
        print(f"Ошибка при запросе к Gemini: {e}")
        await message.answer("⚠️ Извини, произошла ошибка при обработке запроса. Попробуй еще раз.")


# --- ФЕЙКОВЫЙ СЕРВЕР ДЛЯ ОБМАНА RENDER (БЕСПЛАТНЫЙ ТАРИФ) ---
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
    # Render автоматически передает нужный порт в переменные окружения
    port = int(os.environ.get("PORT", 8000))
    server = await asyncio.start_server(handle_ping, '0.0.0.0', port)
    print(f"Фейковый веб-сервер запущен на порту {port}")
    async with server:
        await server.serve_forever()
# ------------------------------------------------------------


# Главная функция запуска
async def main():
    # Запускаем веб-сервер фоном, чтобы Render не ругался на порты
    asyncio.create_task(start_dummy_server())
    
    # Запускаем прослушивание сообщений Telegram
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
