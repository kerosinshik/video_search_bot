from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from bot.handlers import start, help_command, search_videos, handle_text, search_platform, list_available_formats
from config import BOT_TOKEN
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

yt_dlp_logger = logging.getLogger('yt_dlp')
yt_dlp_logger.setLevel(logging.WARNING)

def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f"Update {update} caused error {context.error}")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("formats", list_available_formats))
    dp.add_handler(CallbackQueryHandler(search_platform, pattern='^search_'))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    # Добавляем обработчик ошибок
    dp.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()