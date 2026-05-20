from datetime import datetime, timedelta
import re
from typing import Optional


def parse_datetime(user_input: str) -> Optional[datetime]:
    """
    Парсит дату и время из строки пользователя.
    Поддерживаемые форматы:
    - ГГГГ-ММ-ДД ЧЧ:ММ
    - завтра ЧЧ:ММ
    - через N часов
    - через N минут
    """
    user_input = user_input.lower().strip()
    now = datetime.now()
    
    # Формат: ГГГГ-ММ-ДД ЧЧ:ММ
    match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2})', user_input)
    if match:
        year, month, day, hour, minute = map(int, match.groups())
        try:
            return datetime(year, month, day, hour, minute)
        except ValueError:
            return None
    
    # Формат: завтра ЧЧ:ММ
    match = re.match(r'завтра\s+(\d{1,2}):(\d{1,2})', user_input)
    if match:
        hour, minute = map(int, match.groups())
        tomorrow = now + timedelta(days=1)
        return datetime(tomorrow.year, tomorrow.month, tomorrow.day, hour, minute)
    
    # Формат: через N часов
    match = re.match(r'через\s+(\d+)\s+часов?', user_input)
    if match:
        hours = int(match.group(1))
        return now + timedelta(hours=hours)
    
    # Формат: через N минут
    match = re.match(r'через\s+(\d+)\s+минут?', user_input)
    if match:
        minutes = int(match.group(1))
        return now + timedelta(minutes=minutes)
    
    return None


def format_reminder_time(remind_time: datetime) -> str:
    """Форматирует время напоминания для отображения пользователю"""
    return remind_time.strftime("%d.%m.%Y в %H:%M")
