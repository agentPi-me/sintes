from telegram import Update
from telegram.ext import ContextTypes

from user_data import add_user, get_user_count

START_MESSAGE = """
Добро пожаловать в Sintes!

Я помогу вам управлять вашим расписанием через Google Календарь. 
Для начала работы необходимо:

1️⃣ Авторизоваться через Google (/authorize)
2️⃣ Установить часовой пояс (/set_timezone)

После этого вы сможете добавлять события голосовыми сообщениями.
Нужна помощь? Используйте команду /help
"""

HELP_MESSAGE = r"""
🎯 *Руководство по использованию бота*

*Основные команды:*
• /start \- Перезапуск бота
• /authorize \- Подключение к Google Calendar
• /set\_timezone \- Настройка часового пояса
• /help \- Это руководство

*Как добавить событие:*
Напишите или отправьте голосовое сообщение в одном из форматов:

*Примеры команд:*
• "Сегодня с 10:00 до 12:00 Встреча"
• "Завтра с 14:30 до 15:30 Совещание"
• "Послезавтра с 09:00 до 10:00 Звонок"

*Советы:*
• Говорите чётко и разборчиво
• Указывайте время в 24\-часовом формате
• Название события произносите в конце

❓ Вопросы? Пишите: mamishka79@gmail.com
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username or "Без никнейма"  # Если никнейм отсутствует
    add_user(user_id, username)  # Сохраняем никнейм пользователя
    await update.message.reply_text(START_MESSAGE)

async def user_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    count = get_user_count()
    await update.message.reply_text(f"Количество зарегистрированных пользователей: {count}")
    
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text(
            text=HELP_MESSAGE,
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        await update.message.reply_text(
            text=HELP_MESSAGE.replace('*', '').replace('\\', ''),
            parse_mode=None
        )