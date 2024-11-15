import re
from googleapiclient.discovery import build
import pytz
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
import speech_recognition as sr
from pydub import AudioSegment
from settings import user_timezones, user_credentials
from logger import logger

VOICE_FILE_OGA = 'voice.oga'
VOICE_FILE_WAV = 'voice.wav'

ERROR_MESSAGES = {
    'invalid_format': "❌ Некорректный формат команды. Попробуйте еще раз.",
    'invalid_time': "❌ Время окончания должно быть позже времени начала.",
    'no_auth': "❌ Сначала выполните команду /authorize.",
    'event_error': "❌ Ошибка при добавлении события.",
    'no_voice': "❌ Не удалось получить голосовое сообщение.",
    'download_error': "❌ Ошибка при загрузке файла: {}",
    'convert_error': "❌ Ошибка при конвертации файла: {}",
    'recognition_error': "❌ Не удалось распознать голосовое сообщение.",
    'service_error': "❌ Ошибка сервиса распознавания: {}"
}

DATE_TIME_PATTERN = re.compile(
    r"(?P<date>сегодня|завтра|послезавтра|пустым\sоставить|на\sследующей\sнеделе|"
    r"через\s(два|три)\s(дня|недели|месяца|года)|\d{1,2}\s[а-я]+\s\d{4})\s+"
    r"(?:с|от)?\s*(?P<start_hour>\d{1,2}):?(?P<start_min>\d{2})?\s*(?:-|до)?\s*"
    r"(?P<end_hour>\d{1,2}):?(?P<end_min>\d{2})?\s*(?P<title>.+)|"
    r"(?P<today_with_time>сегодня\s+с\s(?P<start_hour_2>\d{1,2}):?(?P<start_min_2>\d{2})?\s+"
    r"до\s+(?P<end_hour_2>\d{1,2}):?(?P<end_min_2>\d{2})?\s(?P<title_2>.+))"
)

def parse_time(match):
    start_hour = int(match.group("start_hour") or match.group("start_hour_2") or 0)
    start_min = int(match.group("start_min") or match.group("start_min_2") or 0)
    end_hour = int(match.group("end_hour") or match.group("end_hour_2") or 0)
    end_min = int(match.group("end_min") or match.group("end_min_2") or 0)
    return start_hour, start_min, end_hour, end_min

def get_event_date(date_text: str, today: datetime.date) -> datetime.date:
    date_mapping = {
        "сегодня": today,
        "пустым оставить": today,
        "завтра": today + timedelta(days=1),
        "послезавтра": today + timedelta(days=2),
    }
    
    if date_text in date_mapping:
        return date_mapping[date_text]
    elif "через" in date_text:
        days = 2 if "два" in date_text else 3
        return today + timedelta(days=days)
    
    return today

async def handle_error(update: Update, message: str):
    await update.message.reply_text(message)

async def add_event_to_calendar(service, event: dict) -> str:
    event_result = service.events().insert(calendarId='primary', body=event).execute()
    return f'✅ Событие добавлено: {event_result.get("htmlLink")}'

async def add_event_from_voice(update: Update, message_text: str) -> None:
    user_id = update.effective_user.id
    timezone = user_timezones.get(user_id, 'UTC')
    tz = pytz.timezone(timezone)
    
    pattern = DATE_TIME_PATTERN
    match = pattern.search(message_text)

    if not match:
        await handle_error(update, ERROR_MESSAGES['invalid_format'])
        return

    start_hour, start_min, end_hour, end_min = parse_time(match)
    title = (match.group("title") or match.group("title_2")).strip()
    date_text = match.group("date")
    today = datetime.now(tz).date()
    event_date = get_event_date(date_text, today)

    event_start = tz.localize(datetime.combine(event_date, datetime.min.time()) + timedelta(hours=start_hour, minutes=start_min))
    event_end = tz.localize(datetime.combine(event_date, datetime.min.time()) + timedelta(hours=end_hour, minutes=end_min))

    if event_end <= event_start:
        await handle_error(update, ERROR_MESSAGES['invalid_time'])
        return

    try:
        credentials = user_credentials.get(user_id)
        if not credentials:
            await handle_error(update, ERROR_MESSAGES['no_auth'])
            return

        service = build('calendar', 'v3', credentials=credentials)
        event = {
            'summary': title,
            'start': {'dateTime': event_start.isoformat(), 'timeZone': timezone},
            'end': {'dateTime': event_end.isoformat(), 'timeZone': timezone},
        }
        event_result = service.events().insert(calendarId='primary', body=event).execute()
        await update.message.reply_text(f'✅ Событие добавлено: {event_result.get("htmlLink")}')
    except Exception as e:
        await handle_error(update, ERROR_MESSAGES['event_error'])
        logger.error(f"Ошибка при добавлении события: {e}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    voice = update.message.voice
    if voice is None:
        await handle_error(update, ERROR_MESSAGES['no_voice'])
        return
    
    voice_file = await voice.get_file()

    try:
        await voice_file.download_to_drive('voice.oga')
    except Exception as e:
        await handle_error(update, f"❌ Ошибка при загрузке файла: {e}")
        return

    try:
        audio = AudioSegment.from_ogg('voice.oga')
        audio.export('voice.wav', format='wav')
    except Exception as e:
        await handle_error(update, f"❌ Ошибка при конвертации файла: {e}")
        return

    recognizer = sr.Recognizer()
    with sr.AudioFile('voice.wav') as source:
        audio_data = recognizer.record(source)
        try:
            message_text = recognizer.recognize_google(audio_data, language='ru-RU')
            await update.message.reply_text(f"Вы сказали: {message_text}")
            await add_event_from_voice(update, message_text)
        except sr.UnknownValueError:
            await handle_error(update, ERROR_MESSAGES['recognition_error'])
        except sr.RequestError as e:
            await handle_error(update, f"❌ Ошибка сервиса распознавания: {e}")
        except Exception as e:
            await handle_error(update, f"❌ Произошла ошибка: {str(e)}")
            logger.error(f"Ошибка при обработке голосового сообщения: {str(e)}")