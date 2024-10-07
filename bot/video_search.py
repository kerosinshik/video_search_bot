from googleapiclient.discovery import build
import re
from pytube import YouTube
from datetime import timedelta
import pytz
from telegram import Update
from telegram.ext import CallbackContext

# Импортируем конфигурацию
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GOOGLE_API_KEY, GOOGLE_CSE_ID, MAX_RESULTS

# Константа для максимальной длительности короткого видео (в секундах)
MAX_SHORT_VIDEO_DURATION = 60 * 5  # 5 минут


def is_valid_video(video):
    try:
        yt = YouTube(video['link'])
        return yt.length <= MAX_SHORT_VIDEO_DURATION
    except:
        return False


def extract_video_info(item):
    return {
        'title': item.get('title', 'Без названия'),
        'link': item.get('link', ''),
        'snippet': item.get('snippet', '')
    }


def search_and_send_videos(update: Update, context: CallbackContext, query: str, platform: str):
    videos = search_videos(query, platform)
    sent_count = 0
    for video in videos:
        if is_valid_video(video):
            send_video_info(update, context, video)
            sent_count += 1
            if sent_count >= MAX_RESULTS:
                break

    if sent_count == 0:
        update.message.reply_text(
            "К сожалению, не удалось найти подходящих коротких видео по вашему запросу."
        )


def search_videos(query, platform):
    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
    search_query = f"{query} site:{platform}.com short OR shorts OR reels"

    try:
        res = service.cse().list(q=search_query, cx=GOOGLE_CSE_ID, num=MAX_RESULTS * 2).execute()
        return [extract_video_info(item) for item in res.get('items', [])]
    except Exception as e:
        print(f"An error occurred during search: {e}")
        return []


def send_video_info(update: Update, context: CallbackContext, video):
    try:
        yt = YouTube(video['link'])
        moscow_tz = pytz.timezone('Europe/Moscow')
        publish_date = yt.publish_date.astimezone(moscow_tz) if yt.publish_date else None

        duration = str(timedelta(seconds=yt.length))

        message = (f"Найдено короткое видео: {video['title']}\n")

        if publish_date:
            message += f"Опубликовано: {publish_date.strftime('%d.%m.%Y %H:%M')} (МСК)\n"
        else:
            message += "Дата публикации недоступна\n"

        message += f"Длительность: {duration}\n{video['link']}"

        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    except Exception as e:
        print(f"Error sending video info: {e}")
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Найдено видео: {video['title']}\n{video['link']}"
        )


def is_video_url(url):
    youtube_pattern = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    tiktok_pattern = r'https?://(?:www\.)?tiktok\.com/(@[\w.-]+/video/\d+|\w+/video/\d+)'
    instagram_pattern = r'https?://(?:www\.)?instagram\.com/(p|reel|tv)/[\w-]+'

    return (re.match(youtube_pattern, url) or
            re.match(tiktok_pattern, url) or
            re.match(instagram_pattern, url))


# Дополнительные функции, если они нужны

def get_video_info(video_url):
    try:
        yt = YouTube(video_url)
        moscow_tz = pytz.timezone('Europe/Moscow')
        publish_date = yt.publish_date.astimezone(moscow_tz) if yt.publish_date else None
        duration = str(timedelta(seconds=yt.length)) if yt.length else "Неизвестно"

        return {
            'title': yt.title,
            'publish_date': publish_date,
            'duration': duration,
            'url': video_url
        }
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None


def format_video_info(video_info):
    if not video_info:
        return "Не удалось получить информацию о видео."

    message = f"Видео: {video_info['title']}\n"
    if video_info['publish_date']:
        message += f"Опубликовано: {video_info['publish_date'].strftime('%d.%m.%Y %H:%M')} (МСК)\n"
    message += f"Длительность: {video_info['duration']}\n"
    message += f"Ссылка: {video_info['url']}"

    return message