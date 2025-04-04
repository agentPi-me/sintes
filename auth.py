from google_auth_oauthlib.flow import Flow
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from settings import CLIENT_SECRETS_FILE, SCOPES, REDIRECT_URI, auth_flows, user_credentials
from logger import logger

AUTH_MESSAGE = (
    'Нажмите кнопку ниже для авторизации:\n'
    'После авторизации вы будете перенаправлены на страницу, где получите код.\n'
    'Пожалуйста, скопируйте этот код и отправьте его в Telegram, используя команду /auth <код>.'
)
NO_AUTH_MESSAGE = 'Пожалуйста, сначала выполните команду /authorize.'
SUCCESS_MESSAGE = ('✅ Авторизация прошла успешно! '
                   'Теперь вызовите команду /timezone чтобы установить часовой пояс, '
                   'или отправьте своё местоположение.')
ERROR_MESSAGE = '❌ Ошибка авторизации. Попробуйте снова.'

async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, 
        scopes=SCOPES, 
        redirect_uri=REDIRECT_URI
    )
    auth_flows[user_id] = flow
    authorization_url, _ = flow.authorization_url()

    keyboard = [[InlineKeyboardButton("Авторизоваться", url=authorization_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(AUTH_MESSAGE, reply_markup=reply_markup)

async def handle_auth_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("❌ Пожалуйста, укажите код авторизации после команды.")
        return

    code = ' '.join(context.args).strip()

    logger.info(f"Received authorization code from user {user_id}: {code}")

    if user_id not in auth_flows:
        logger.warning(f"No auth flow found for user {user_id}.")
        await update.message.reply_text(NO_AUTH_MESSAGE)
        return

    flow = auth_flows.pop(user_id)

    try:
        flow.fetch_token(code=code)
        user_credentials[user_id] = flow.credentials
        await update.message.reply_text(SUCCESS_MESSAGE)
        logger.info(f"User   {user_id} authorized successfully.")
    except Exception as e:
        await update.message.reply_text(ERROR_MESSAGE)
        logger.error(f'Authorization error for user {user_id}: {e}')