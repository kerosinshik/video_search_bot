from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CallbackQueryHandler
from .video_search import search_and_send_videos, is_video_url, get_video_info, format_video_info
from googletrans import Translator
import yt_dlp
import os
import pytz
from datetime import datetime, timedelta
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

translator = Translator()


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        ['🔍 Поиск видео', '📥 Скачать и отправить'],
        ['📋 Форматы видео', 'ℹ️ Помощь']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text('Привет! Я бот для поиска и скачивания коротких видео. Выберите действие:',
                              reply_markup=reply_markup)


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Нажмите "🔍 Поиск видео" и введите ключевые слова для поиска. '
                              'Для скачивания видео нажмите "📥 Скачать и отправить" и отправьте ссылку на видео YouTube.')


def search_videos(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("YouTube", callback_data='search_youtube'),
         InlineKeyboardButton("TikTok", callback_data='search_tiktok'),
         InlineKeyboardButton("Instagram", callback_data='search_instagram')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите платформу для поиска:', reply_markup=reply_markup)
    context.user_data['expecting'] = 'search_platform'


def handle_search_query(update: Update, context: CallbackContext) -> None:
    query = update.message.text
    platform = context.user_data.get('search_platform', 'youtube')
    update.message.reply_text(f'Ищу видео на {platform} по запросу: {query}')
    search_and_send_videos(update, context, query, platform)

def search_platform(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    platform = query.data.split('_')[1]
    query.edit_message_text(f"Введите ключевые слова для поиска на {platform}:")
    context.user_data['search_platform'] = platform
    context.user_data['expecting'] = 'search_query'


def download_video_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Отправьте ссылку на видео YouTube, которое нужно скачать и отправить:')
    context.user_data['expecting'] = 'video_url'


def handle_text(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    user_data = context.user_data

    if text == '🔍 Поиск видео':
        search_videos(update, context)
    elif text == '📥 Скачать и отправить':
        update.message.reply_text('Отправьте ссылку на видео YouTube, которое нужно скачать и отправить:')
        user_data['expecting'] = 'video_url'
    elif text == '📋 Форматы видео':
        update.message.reply_text('Отправьте ссылку на видео, чтобы увидеть доступные форматы.')
        user_data['expecting'] = 'video_formats'
    elif text == 'ℹ️ Помощь':
        help_command(update, context)
    elif user_data.get('expecting') == 'search_query':
        handle_search_query(update, context)
    elif user_data.get('expecting') == 'video_url':
        download_and_send_video(update, context)
    elif user_data.get('expecting') == 'video_formats':
        list_available_formats(update, context)
    elif is_video_url(text):  # Добавляем проверку, является ли текст URL видео
        download_and_send_video(update, context)
    else:
        update.message.reply_text('Пожалуйста, выберите действие из меню.')

    # Сбрасываем ожидание после обработки, кроме случая ожидания URL видео
    if user_data.get('expecting') != 'video_url':
        user_data['expecting'] = None


def handle_search_query(update: Update, context: CallbackContext) -> None:
    query = update.message.text
    platform = context.user_data.get('search_platform', 'youtube')
    translated_query = translator.translate(query, dest='en').text
    update.message.reply_text(f'Ищу видео на {platform} по запросу: {query}')
    search_and_send_videos(update, context, translated_query, platform)
    context.user_data['expecting'] = None


def download_and_send_video(update: Update, context: CallbackContext) -> None:
    video_url = update.message.text

    if not is_video_url(video_url):
        update.message.reply_text('Пожалуйста, отправьте корректную ссылку на видео YouTube.')
        return

    try:
        update.message.reply_text('Начинаю загрузку видео...')
        video_file = download_youtube_video(video_url)

        if video_file and os.path.exists(video_file):
            file_size = os.path.getsize(video_file)
            logger.info(f"Video file size: {file_size} bytes")

            if file_size > 50 * 1024 * 1024:  # Если файл больше 50 МБ
                update.message.reply_text('Видео слишком большое для отправки в Telegram. Максимальный размер - 50 МБ.')
            else:
                with open(video_file, 'rb') as file:
                    update.message.reply_video(video=file, supports_streaming=True)
                update.message.reply_text('Видео успешно отправлено.')

            os.remove(video_file)
        else:
            update.message.reply_text('Не удалось загрузить видео. Попробуйте другую ссылку.')
    except Exception as e:
        logger.error(f"Error in download_and_send_video: {str(e)}", exc_info=True)
        update.message.reply_text(f'Произошла ошибка при обработке видео: {str(e)}')

    # Сбрасываем ожидание после обработки
    context.user_data['expecting'] = None


def download_youtube_video(video_url):
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',  # Пробуем сначала лучший MP4
            'outtmpl': '%(title)s.%(ext)s',
            'verbose': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                logger.info(f"Attempting to download video: {video_url}")
                info = ydl.extract_info(video_url, download=True)
            except yt_dlp.utils.ExtractorError:
                logger.info("Failed with MP4, trying any format")
                ydl_opts['format'] = 'best'  # Пробуем любой лучший формат
                info = ydl.extract_info(video_url, download=True)

            if info is None:
                logger.error("Failed to extract video info")
                return None

            filename = ydl.prepare_filename(info)
            logger.info(f"Video downloaded: {filename}")
            return filename
    except Exception as e:
        logger.error(f"Error in download_youtube_video: {str(e)}", exc_info=True)
    return None


def list_available_formats(update: Update, context: CallbackContext) -> None:
    if not context.args:
        update.message.reply_text("Пожалуйста, укажите URL видео после команды.")
        return

    video_url = context.args[0]
    ydl_opts = {'logger': logger}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats = info.get('formats', [])

            if not formats:
                update.message.reply_text("Не удалось получить информацию о форматах для этого видео.")
                return

            format_list = ["Доступные форматы:"]
            for f in formats:
                format_info = f"ID: {f.get('format_id')} - {f.get('ext')} - {f.get('resolution')} - видео: {f.get('vcodec')} - аудио: {f.get('acodec')}"
                format_list.append(format_info)

            update.message.reply_text("\n".join(format_list[:30]))  # Ограничиваем вывод 30 форматами
    except Exception as e:
        logger.error(f"Error in list_available_formats: {str(e)}", exc_info=True)
        update.message.reply_text(f"Произошла ошибка при получении форматов: {str(e)}")


def help_command(update: Update, context: CallbackContext) -> None:
    help_text = """
    Доступные команды:
    /start - Начать работу с ботом
    /help - Показать это сообщение
    /formats <url> - Показать доступные форматы для видео

    Для поиска видео нажмите "🔍 Поиск видео" и введите ключевые слова.
    Для скачивания видео нажмите "📥 Скачать и отправить" и отправьте ссылку на видео YouTube.
    """
    update.message.reply_text(help_text)