from telegram import Update
from telegram.ext import ContextTypes
from user_data import add_user, get_user_count, add_start_count, get_unique_start_count

START_MESSAGE = """
Добро пожаловать в Sintes!

Я помогу вам управлять вашим расписанием через Google Календарь. 
Для начала работы необходимо:

1️⃣ Авторизоваться через Google (/authorize)
2️⃣ Установить часовой пояс (/timezone)

После этого вы сможете добавлять события голосовыми сообщениями.
Нужна помощь? Используйте команду /help
"""

HELP_MESSAGE = r"""
🎯 *Руководство по использованию бота*

*Основные команды:*
• /start \- Перезапуск бота
• /authorize \- Подключение к Google Calendar
• /timezone \- Настройка часового пояса
• /edit \- Редактирование события
• /help \- Это руководство

*Как добавить событие:*
Напишите или отправьте голосовое сообщение в одном из форматов:

*Примеры команд:*
• "Сегодня с 10:00 до 12:00 Встреча"
• "Завтра с 14:30 до 15:30 Совещание"

*Редактирование события:*
• /edit [ID события] [новое название]
• Пример: /edit abc123 Важное совещание

*Советы:*
• Говорите чётко и разборчиво
• Указывайте время в 24\-часовом формате
• Название события произносите в конце
• ID события можно найти по ссылке после создания

❓ Вопросы? Пишите: mamishka79@gmail.com
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username or "Без никнейма"
    
    # Добавляем пользователя в базу
    add_user(user_id, username)
    
    # Получаем количество нажатий /start
    is_new_start = add_start_count(user_id)
    unique_start_count = get_unique_start_count()
    
    # Формируем сообщение
    welcome_message = f"{START_MESSAGE}\n\n" \
                      f"Количество зарегистрированных пользователей: {get_user_count()}\n" \
                      f"Уникальных пользователей, нажавших /start: {unique_start_count}"
    
    await update.message.reply_text(welcome_message)
     
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