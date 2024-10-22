import os
import re
import pickle
import logging
import tempfile
import datetime
import subprocess
from dateutil import parser
import speech_recognition as sr
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton

from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, 
    CallbackContext, ConversationHandler
)

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "7931196709:AAGdsl3Ctdc30uBDrxf-C-XbcYaEcxj2nWY"
SCOPES = ['https://www.googleapis.com/auth/calendar']
ASK_AUTH_CODE = 1

def _get_token_filename(user_id):
    """Создает уникальное имя файла для хранения токена пользователя."""
    return f"token_{user_id}.pickle"

def _load_credentials(user_id):
    """Загружает учетные данные для конкретного пользователя."""
    token_filename = _get_token_filename(user_id)
    if os.path.exists(token_filename):
        with open(token_filename, 'rb') as token_file:
            return pickle.load(token_file)
    return None

def _save_credentials(user_id, creds):
    """Сохраняет учетные данные для пользователя."""
    token_filename = _get_token_filename(user_id)
    with open(token_filename, 'wb') as token_file:
        pickle.dump(creds, token_file)

async def authorize_google_calendar(update: Update, context: CallbackContext):
    """Инициализация авторизации пользователя."""
    user_id = update.message.from_user.id
    creds = _load_credentials(user_id)
    if creds:
        await update.message.reply_text("Вы уже авторизованы в Google Calendar.")
        return ConversationHandler.END

    flow = _init_flow()
    auth_url, _ = flow.authorization_url(prompt='consent')
    await update.message.reply_text(
        f'Перейдите по следующей ссылке для авторизации: {auth_url}\nВведите код сюда:'
    )

    context.user_data['flow'] = flow  # Сохраняем поток авторизации
    return ASK_AUTH_CODE

def _init_flow():
    """Инициализация OAuth2 потока с использованием локального перенаправления."""
    return Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=SCOPES,
        redirect_uri='https://8f6c-176-64-16-51.ngrok-free.app'
    )

async def handle_auth_code(update: Update, context: CallbackContext):
    """Обработка кода авторизации и сохранение токенов."""
    user_id = update.message.from_user.id
    flow = context.user_data.get('flow')
    if not flow:
        await update.message.reply_text("Произошла ошибка. Начните заново с /setup_calendar.")
        return ConversationHandler.END

    flow.fetch_token(code=update.message.text)
    creds = flow.credentials
    _save_credentials(user_id, creds)
    await update.message.reply_text("Интеграция с Google Calendar завершена!")

async def start(update: Update, context: CallbackContext):
    """Стартовое сообщение бота."""
    keyboard = [
        [KeyboardButton("Отправить местоположение", request_location=True)],
        ["/setup_calendar", "/add_task", "/plan_day", "/delete_task", "/help"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Я бот для планирования. Интеграция с Google Calendar поможет управлять вашими задачами.",
        reply_markup=reply_markup
    )

def get_calendar_service(user_id):
    """Получение объекта сервиса Google Calendar для пользователя."""
    creds = _load_credentials(user_id)
    if creds:
        return build('calendar', 'v3', credentials=creds)
    return None

async def add_task(update: Update, context: CallbackContext):
    """Добавление задачи в Google Calendar."""
    user_input = ' '.join(context.args)
    if not user_input:
        await update.message.reply_text("Используйте формат '/add_task <дата> <время> <описание> <цвет>'.")
        return

    try:
        user_id = update.message.from_user.id
        logger.info(f"Получен ввод: {user_input}")

        time_match = re.search(r'\b(\d{1,2}:\d{2})\s*до\s*(\d{1,2}:\d{2})\b', user_input)
        if not time_match:
            await update.message.reply_text("Укажите время в формате 'с 14:00 до 15:00'.")
            return

        start_time, end_time = _parse_task_times(time_match.groups(), user_input)
        task_description = _clean_task_description(user_input)
        color_id = _get_color_id(user_input)

        service = get_calendar_service(user_id)
        if not service:
            await update.message.reply_text("Ошибка подключения к Google Calendar.")
            return

        event = {
            'summary': task_description,
            'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Asia/Almaty'},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Asia/Almaty'}
        }
        if color_id:
            event['colorId'] = color_id

        service.events().insert(calendarId='primary', body=event).execute()
        await update.message.reply_text(f"Задача добавлена: {task_description} с {start_time.strftime('%H:%M')} до {end_time.strftime('%H:%M')}.")

    except Exception as e:
        logger.error("Ошибка при добавлении задачи", exc_info=True)
        await update.message.reply_text("Произошла ошибка при добавлении задачи.")

async def voice_message(update: Update, context: CallbackContext):
    """Обработка голосовых сообщений и добавление задачи."""
    try:
        file = await context.bot.get_file(update.message.voice.file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
            await file.download_to_drive(temp_file.name)

        wav_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
        subprocess.run(['ffmpeg', '-y', '-i', temp_file.name, wav_file], check=True)

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_file) as source:
            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(audio_data, language='ru-RU')
        context.args = text.split()
        await add_task(update, context)

    except Exception as e:
        logger.error("Ошибка при обработке аудио", exc_info=True)
        await update.message.reply_text("Произошла ошибка при обработке аудио.")

def _parse_task_times(times, user_input):
    start_time_str, end_time_str = times
    now = datetime.datetime.now()
    is_tomorrow = 'завтра' in user_input.lower()
    start_time = parser.parse(start_time_str).replace(year=now.year, month=now.month, day=now.day)
    end_time = parser.parse(end_time_str).replace(year=now.year, month=now.month, day=now.day)
    if is_tomorrow:
        start_time += datetime.timedelta(days=1)
        end_time += datetime.timedelta(days=1)
    return start_time, end_time

def _clean_task_description(user_input):
    cleaned_input = re.sub(r'(завтра\s*)?(с\s*\d{1,2}:\d{2}\s*до\s*\d{1,2}:\d{2})', '', user_input, count=1).strip()
    cleaned_input = re.sub(r'цвет\s+\w+', '', cleaned_input, count=1).strip()
    return cleaned_input

def _get_color_id(user_input):
    color_map = {'красный': '11', 'синий': '9', 'зелёный': '10'}
    match = re.search(r'цвет\s+(\w+)', user_input.lower())
    return color_map.get(match.group(1)) if match else None

SELECT_TASK, EDIT_FIELD, UPDATE_TASK = range(3)

async def edit_task(update: Update, context: CallbackContext):
    """Начало процесса редактирования задачи."""
    user_input = ' '.join(context.args)
    if not user_input:
        await update.message.reply_text("Введите название или дату задачи: /edit_task <название> или <дата>")
        return ConversationHandler.END

    user_id = update.message.from_user.id
    service = get_calendar_service(user_id)

    if not service:
        await update.message.reply_text("Ошибка подключения к Google Calendar.")
        return ConversationHandler.END

    # Ищем задачу по запросу пользователя
    events_result = service.events().list(
        calendarId='primary', q=user_input, singleEvents=True
    ).execute()
    events = events_result.get('items', [])

    if not events:
        await update.message.reply_text("Задача не найдена.")
        return ConversationHandler.END

    # Если найдена одна задача — продолжаем, иначе показываем список
    if len(events) == 1:
        context.user_data['event'] = events[0]
        return await ask_edit_option(update, context)
    else:
        event_list = [
            f"{i + 1}. {event['summary']} — {event['start'].get('dateTime', event['start'].get('date'))}"
            for i, event in enumerate(events)
        ]
        await update.message.reply_text(
            "Найдено несколько задач. Укажите номер задачи:\n" + "\n".join(event_list)
        )
        context.user_data['events'] = events
        return SELECT_TASK

async def select_task(update: Update, context: CallbackContext):
    """Выбор задачи из списка."""
    try:
        selected_index = int(update.message.text) - 1
        context.user_data['event'] = context.user_data['events'][selected_index]
        return await ask_edit_option(update, context)
    except (ValueError, IndexError):
        await update.message.reply_text("Некорректный номер задачи. Попробуйте снова.")
        return SELECT_TASK

async def ask_edit_option(update: Update, context: CallbackContext):
    """Запрос на выбор, что изменить в задаче."""
    keyboard = [
        [InlineKeyboardButton("Название", callback_data='edit_title')],
        [InlineKeyboardButton("Дата", callback_data='edit_date')],
        [InlineKeyboardButton("Время", callback_data='edit_time')],
        [InlineKeyboardButton("Цвет", callback_data='edit_color')],
        [InlineKeyboardButton("Удалить", callback_data='delete_task')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Что вы хотите изменить?", reply_markup=reply_markup)
    return EDIT_FIELD

async def handle_edit_option(update: Update, context: CallbackContext):
    """Обработка выбранного поля для редактирования."""
    query = update.callback_query
    await query.answer()

    option = query.data
    context.user_data['edit_option'] = option

    if option == 'edit_title':
        await query.edit_message_text("Введите новое название:")
    elif option == 'edit_date':
        await query.edit_message_text("Введите новую дату (например, 23 октября):")
    elif option == 'edit_time':
        await query.edit_message_text("Введите новое время (например, 14:00 до 15:00):")
    elif option == 'edit_color':
        await query.edit_message_text("Введите новый цвет (например, красный, синий, зелёный):")
    elif option == 'delete_task':
        return await delete_task(update, context)

    return UPDATE_TASK

async def update_task(update: Update, context: CallbackContext):
    """Внесение изменений в задачу."""
    user_id = update.message.from_user.id
    service = get_calendar_service(user_id)
    event = context.user_data['event']
    option = context.user_data['edit_option']
    new_value = update.message.text

    try:
        if option == 'edit_title':
            event['summary'] = new_value
        elif option == 'edit_date':
            new_date = parser.parse(new_value).date().isoformat()
            event['start']['date'] = new_date
            event['end']['date'] = new_date
        elif option == 'edit_time':
            start_time, end_time = _parse_task_times(new_value.split(' до '), new_value)
            event['start']['dateTime'] = start_time.isoformat()
            event['end']['dateTime'] = end_time.isoformat()
        elif option == 'edit_color':
            color_id = _get_color_id(new_value)
            if color_id:
                event['colorId'] = color_id
            else:
                await update.message.reply_text("Некорректный цвет. Попробуйте снова.")
                return UPDATE_TASK

        service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()
        await update.message.reply_text("Задача успешно обновлена!")
    except Exception as e:
        logger.error("Ошибка при обновлении задачи", exc_info=True)
        await update.message.reply_text("Произошла ошибка при обновлении задачи.")
    return ConversationHandler.END

async def delete_task(update: Update, context: CallbackContext):
    """Удаление задачи."""
    user_id = update.message.from_user.id
    service = get_calendar_service(user_id)
    event = context.user_data['event']

    service.events().delete(calendarId='primary', eventId=event['id']).execute()
    await update.callback_query.edit_message_text(f"Задача '{event['summary']}' удалена.")
    return ConversationHandler.END

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Обработчик команды /setup_calendar
    conv_handler_calendar = ConversationHandler(
        entry_points=[CommandHandler("setup_calendar", authorize_google_calendar)],
        states={ASK_AUTH_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_auth_code)]},
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("Отменено."))]
    )

    # Обработчик команды /edit_task
    conv_handler_edit = ConversationHandler(
        entry_points=[CommandHandler("edit_task", edit_task)],
        states={
            SELECT_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_task)],
            EDIT_FIELD: [CallbackQueryHandler(handle_edit_option)],
            UPDATE_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_task)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("Отменено."))]
    )

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_task", add_task))
    application.add_handler(MessageHandler(filters.VOICE, voice_message))

    # Добавляем ConversationHandlers
    application.add_handler(conv_handler_calendar)
    application.add_handler(conv_handler_edit)

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
