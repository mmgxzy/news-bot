import sqlite3
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.dispatcher.filters import Command
from aiogram import executor
from config import token

# Инициализация бота и диспетчера
bot = Bot(token=token)
dp = Dispatcher(bot)

# Создание базы данных и таблицы, если они не существуют
def init_db():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Добавление новости в базу данных
def add_news_to_db(title, url):
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO news (title, url) VALUES (?, ?)', (title, url))
    conn.commit()
    conn.close()

# Функция для обработки команды /start
async def start(message: Message):
    await message.answer("Привет! Я бот новостей. Чтобы получить новости, введите команду /news.")

# Функция для обработки команды /news
async def news(message: Message):
    # Проходим по страницам с новостями
    for page in range(1, 11):
        url = f'https://24.kg/page_{page}'
        try:
            # Запрос к веб-сайту
            response = requests.get(url=url)
            response.raise_for_status()  # Проверка успешности запроса
            # Парсинг HTML с помощью BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            # Поиск всех новостей на странице
            all_news = soup.find_all('div', class_='one')
            # Отправка каждой новости пользователю и сохранение в базу данных
            for news_item in all_news:
                news_title_div = news_item.find('div', class_='title')
                news_link = news_item.find('a')
                if news_title_div and news_link:
                    news_title = news_title_div.text.strip()
                    news_url = f"https://24.kg{news_link['href']}"  # Добавление полного URL
                    # Сохранение новости в базу данных
                    add_news_to_db(news_title, news_url)
                    # Форматирование текста новости
                    news_text = f"*{news_title}*"  # Убираем URL, оставляем только заголовок
                    # Разбиваем текст новости на части длиной не более 4096 символов
                    while len(news_text) > 0:
                        await message.answer(news_text[:4096], parse_mode="Markdown")
                        news_text = news_text[4096:]
        except Exception as e:
            # Обработка ошибок и отправка сообщения об ошибке
            await message.answer(f"Произошла ошибка при получении новостей: {e}")

# Регистрация обработчиков
dp.message_handler(Command('start'))(start)
dp.message_handler(Command('news'))(news)

# Запуск бота
if __name__ == '__main__':
    init_db()  # Инициализация базы данных
    executor.start_polling(dp, skip_updates=True)
