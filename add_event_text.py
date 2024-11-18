import re
from googleapiclient.discovery import build
import pytz
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from settings import user_timezones, user_credentials
from logger import logger

ERROR_MESSAGES = {
    'invalid_format': "❌ Некорректный формат команды. Попробуйте еще раз.",
    'invalid_time': "❌ Время окончания должно быть позже времени начала.",
    'no_auth': "❌ Сначала выполните команду /authorize.",
    'event_error': "❌ Ошибка при добавлении события."
}

DATE_TIME_PATTERN = re.compile(
    r"(?i)(сегодня|завтра|послезавтра)\s+" 
    r"(?:с\s+)?(\d{1,2}):(\d{2})\s+"
    r"(?:до\s+)?(\d{1,2}):(\d{2})\s+"
    r"(.+)"
)

DATE_MAPPING = {
    "сегодня": 0,
    "завтра": 1,
    "послезавтра": 2,
}

def calculate_event_date(date_text: str, today: datetime.date) -> datetime.date:
    if date_text in DATE_MAPPING:
        return today + timedelta(days=DATE_MAPPING[date_text])
    return today

async def add_event_to_calendar(service, event: dict) -> str:
    event_result = service.events().insert(calendarId='primary', body=event).execute()
    return f'✅ Событие добавлено: {event_result.get("htmlLink")}. Используйте /edit_event {event_result.get("id")} для редактирования.'

async def add_event_from_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    message_text = update.message.text.strip().title()

    if user_id not in user_credentials:
        await update.message.reply_text(ERROR_MESSAGES['no_auth'])
        return

    tz = pytz.timezone(user_timezones.get(user_id, 'UTC'))
    logger.info(f"Received text message: {message_text}")

    match = DATE_TIME_PATTERN.match(message_text)
    if not match:
        await update.message.reply_text(ERROR_MESSAGES['invalid_format'])
        return

    date_text, start_hour, start_min, end_hour, end_min, title = match.groups()
    start_hour, start_min, end_hour, end_min = map(int, (start_hour, start_min, end_hour, end_min))

    today = datetime.now(tz).date()
    event_date = calculate_event_date(date_text, today)

    event_start = tz.localize(datetime.combine(event_date, datetime.min.time()) + 
        timedelta(hours=start_hour, minutes=start_min))
    event_end = tz.localize(datetime.combine(event_date, datetime.min.time()) + 
        timedelta(hours=end_hour, minutes=end_min))

    if event_end <= event_start:
        await update.message.reply_text(ERROR_MESSAGES['invalid_time'])
        return

    try:
        credentials = user_credentials[user_id]
        service = build('calendar', 'v3', credentials=credentials)
        event = {
            'summary': title.strip(),
            'start': {'dateTime': event_start.isoformat(), 'timeZone': user_timezones[user_id]},  # Используем часовой пояс пользователя
            'end': {'dateTime': event_end.isoformat(), 'timeZone': user_timezones[user_id]},  # Используем часовой пояс пользователя
        }
        await update.message.reply_text(await add_event_to_calendar(service, event))
    except Exception as e:
        await update.message.reply_text(ERROR_MESSAGES['event_error'])
        logger.error(f"Ошибка при добавлении события: {e}")