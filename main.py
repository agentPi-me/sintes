from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import nest_asyncio
import asyncio

from settings import TELEGRAM_TOKEN
from commands import start, help_command
from auth import authorize, handle_auth_code, register_handlers  # Импортируем register_handlers
from timezone import set_timezone, timezone_button
from add_event_voice import handle_voice
from add_event_text import add_event_from_text
from edit_event import edit_event

def setup_handlers(application):
    handlers = [
        CommandHandler('start', start),
        CommandHandler('help', help_command),
        CommandHandler('authorize', authorize),
        CommandHandler('auth_code', handle_auth_code),
        CommandHandler('set_timezone', set_timezone),
        CommandHandler('edit_event', edit_event),
        CallbackQueryHandler(timezone_button),
        MessageHandler(filters.VOICE, handle_voice),
        MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_from_text),
    ]   
    for handler in handlers:
        application.add_handler(handler)

    # Регистрация дополнительных обработчиков
    register_handlers(application)  # Регистрация команды count_users

async def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    setup_handlers(application)
    await application.run_polling()

if __name__ == '__main__':
    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())