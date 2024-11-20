# user_data.py
import json
import os
import logging
from typing import Dict

USER_DATA_FILE = 'user_data.json'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения данных
USER_DATA: Dict[str, str] = {}

def load_user_data() -> Dict[str, str]:
    global USER_DATA
    logger.info("Загрузка данных пользователей.")
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as file:
                USER_DATA = json.load(file)
        return USER_DATA
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных пользователей: {e}")
        return {}

def save_user_data(user_data: Dict[str, str]):
    global USER_DATA
    USER_DATA = user_data
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as file:
            json.dump(user_data, file, ensure_ascii=False, indent=4)
        logger.info("Данные пользователей сохранены.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных пользователей: {e}")

def add_user(user_id, username):
    user_data = load_user_data()
    if str(user_id) not in user_data:
        user_data[str(user_id)] = username
        save_user_data(user_data)
        logger.info(f"Добавлен новый пользователь: {user_id}")

def get_user_count():
    user_data = load_user_data()
    return len(user_data)