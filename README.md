# Telegram Bot для Поиска Коротких Видео

Этот бот использует Google Custom Search API для поиска интересных коротких видео на YouTube, TikTok и Instagram.

## Функциональность

- Поиск видео на популярных платформах (YouTube Shorts, TikTok, Instagram Reels)
- Отправка ссылок на найденные видео в Telegram

## Установка

1. Клонируйте репозиторий
2. Установите зависимости: `pip install -r requirements.txt`
3. Создайте файл `.env` и добавьте в него необходимые токены:
   ```
   BOT_TOKEN=your_telegram_bot_token
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_CSE_ID=your_google_custom_search_engine_id
   ```
4. Запустите бота: `python main.py`

## Использование

Отправьте боту ключевые слова для поиска видео. Например:
```
/start
Смешные коты
```

## Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.