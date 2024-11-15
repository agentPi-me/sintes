from googleapiclient.discovery import build
from telegram import Update
from telegram.ext import ContextTypes
from settings import user_credentials
from logger import logger


async def edit_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if len(context.args) < 1:
        await update.message.reply_text("❌ Пожалуйста, укажите идентификатор события для редактирования.")
        return

    event_id = context.args[0]
    new_details = ' '.join(context.args[1:]).strip()

    if not new_details:
        await update.message.reply_text("❌ Пожалуйста, укажите новые детали события.")
        return

    credentials = user_credentials.get(user_id)
    if not credentials:
        await update.message.reply_text("❌ Сначала выполните команду /authorize.")
        return

    service = build('calendar', 'v3', credentials=credentials)

    try:
        event = service.events().get(calendarId='primary', eventId=event_id).execute()

        event['summary'] = new_details

        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        await update.message.reply_text(f'✅ Событие обновлено: {updated_event.get("htmlLink")}')
    except Exception as e:
        await update.message.reply_text("❌ Ошибка при редактировании события.")
        logger.error(f"Ошибка при редактировании события: {e}")