import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from google import genai
from config import BOT_TOKEN

# Инициализация бота и диспетчера aiogram
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализируем клиента Gemini (он автоматически возьмет GEMINI_API_KEY из настроек Render)
gemini_client = genai.Client()

# Системная инструкция для роли персонального тренера
SYSTEM_INSTRUCTION = (
    "Ты — квалифицированный, дружелюбный и мотивирующий личный фитнес-тренер "
    "и нутрициолог. Отвечай на вопросы пользователя развернуто, профессионально, "
    "давай практические советы по тренировкам и питанию."
)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я твой персональный ИИ-тренер.\n\n"
        "Задавай мне любые вопросы про тренировки, упражнения, технику выполнения или питание. "
        "Я готов помочь!"
    )

# 🤖 ГЛАВНЫЙ ОБРАБОТЧИК: Запрос к Gemini
@dp.message(F.text)
async def chat_with_gemini(message: types.Message):
    # Показываем пользователю, что бот печатает ответ
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # Используем СТРОГО gemini-2.5-flash, чтобы не вызывать ошибку 404
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=message.text,
            config={
                "system_instruction": SYSTEM_INSTRUCTION,
                "temperature": 0.7
            }
        )
        
        # Отправляем успешный ответ пользователю
        await message.answer(response.text, parse_mode="Markdown")
        
    except Exception as e:
        # Выводим точную ошибку в логи Render, если что-то пойдет не так
        print(f"КРИТИЧЕСКАЯ ОШИБКА GEMINI: {e}")
        await message.answer("⚠️ Извини, произошла ошибка при обработке запроса ИИ. Попробуй еще раз чуть позже.")


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
    
    # Жестко сбрасываем старые зависшие вебхуки/сессии в Telegram, убирая ConflictError
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем чтение сообщений
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
