import os
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

def run_dummy_server():
    # Render автоматически передает нужный порт в переменную окружения PORT
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Фейковый сервер запущен на порту {port}")
    server.serve_forever()

# Запускаем сервер в отдельном потоке, чтобы он не мешал работе бота
threading.Thread(target=run_dummy_server, daemon=True).start()
import asyncio
from aiogram import Bot, Dispatcher, types
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message()
async def handler(message: types.Message):
    await message.answer(f"Получено: {message.text}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
