from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import pytz

user_timezones = {}

def generate_timezone_buttons():
    """Создает кнопки для выбора часового пояса."""
    timezones = pytz.all_timezones  # Используем все доступные часовые пояса из pytz
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(tz, callback_data=tz) for tz in timezones[i:i+4]]
        for i in range(0, len(timezones), 4)
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
    await query.edit_message_text(f"✅ Часовой пояс установлен: {timezone}. Теперь вы можете использовать команду /help для дальнейших инструкций.")

def convert_to_user_timezone(user_id, naive_datetime):
    """Конвертирует время в часовой пояс пользователя."""
    if user_id in user_timezones:
        user_timezone = user_timezones[user_id]
        tz = pytz.timezone(user_timezone)
        local_datetime = tz.localize(naive_datetime)
        return local_datetime
    return naive_datetime