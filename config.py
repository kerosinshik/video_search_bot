import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')

# Bot configuration
MAX_RESULTS = 5
SEARCH_QUERY = '("short video" OR shorts OR reels) site:youtube.com OR site:tiktok.com OR site:instagram.com'