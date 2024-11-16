from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from datetime import datetime
import pytz

user_timezones = {}

def generate_timezone_buttons():
    timezones = [
        "UTC-12", "UTC-11", "UTC-10", "UTC-9",
        "UTC-8", "UTC-7", "UTC-6", "UTC-5",
        "UTC-4", "UTC-3", "UTC-2", "UTC-1",
        "UTC+0", "UTC+1", "UTC+2", "UTC+3",
        "UTC+4", "UTC+5", "UTC+6", "UTC+7",
        "UTC+8", "UTC+9", "UTC+10", "UTC+11",
        "UTC+12", "Asia/Almaty"
    ]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(tz, callback_data=tz) for tz in timezones[i:i+4]]
        for i in range(0, len(timezones), 4)
    ])

async def set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Выберите часовой пояс:", reply_markup=generate_timezone_buttons())

async def timezone_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    timezone = query.data
    user_timezones[query.from_user.id] = timezone
    await query.edit_message_text(f"✅ Часовой пояс установлен: {timezone}. Дальше можете узнать что делать, вызывая команду /help")

def convert_to_user_timezone(user_id, naive_datetime):
    if user_id in user_timezones:
        user_timezone = user_timezones[user_id]
        tz = pytz.timezone(user_timezone)
        local_datetime = tz.localize(naive_datetime)
        return local_datetime
    return naive_datetime