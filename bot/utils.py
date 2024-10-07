from datetime import datetime
import pytz


def is_valid_video(video):
    # Здесь можно добавить дополнительные проверки, например, на длительность видео
    return True


def extract_video_info(item):
    moscow_tz = pytz.timezone('Europe/Moscow')
    publish_date = item.get('pagemap', {}).get('videoobject', [{}])[0].get('uploaddate')

    if publish_date:
        publish_date = datetime.fromisoformat(publish_date).astimezone(moscow_tz)
        formatted_date = publish_date.strftime('%d.%m.%Y %H:%M')
    else:
        formatted_date = 'Дата не указана'

    return {
        'title': item.get('title', 'Без названия'),
        'link': item.get('link', ''),
        'snippet': item.get('snippet', ''),
        'publish_date': formatted_date
    }