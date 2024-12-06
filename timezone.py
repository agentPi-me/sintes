from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import pytz
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_timezones = {}

def generate_timezone_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Алматы (Asia/Almaty)", callback_data="Asia/Almaty")]
    ])

async def set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет сообщение с кнопками для выбора часового пояса."""
    await update.message.reply_text("Выберите часовой пояс:", reply_markup=generate_timezone_buttons())

async def timezone_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатия на кнопки выбора часового пояса."""
    query = update.callback_query
    await query.answer()

    timezone = query.data
    user_timezones[query.from_user.id] = timezone
    logger.info(f"Часовой пояс для пользователя {query.from_user.id} установлен: {timezone}")
    await query.edit_message_text(f"✅ Часовой пояс установлен: {timezone}. Теперь вы можете использовать команду /help для дальнейших инструкций.")

def convert_to_user_timezone(user_id, naive_datetime):
    """Конвертирует время в часовой пояс пользователя."""
    if user_id in user_timezones:
        user_timezone = user_timezones[user_id]
        tz = pytz.timezone(user_timezone)
        local_datetime = tz.localize(naive_datetime)
        logger.info(f"Конвертация времени в часовой пояс пользователя {user_id}: {local_datetime}")
        return local_datetime
    logger.warning(f"Часовой пояс для пользователя {user_id} не установлен. Используется naive_datetime.")
    return naive_datetime