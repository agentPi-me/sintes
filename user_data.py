# user_data.py
import json
import os
import logging

USER_DATA_FILE = 'user_data.json'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_user_data():
    logger.info("Загрузка данных пользователей.")
    if not os.path.exists(USER_DATA_FILE):
        logger.warning("Файл данных пользователей не найден. Создание нового.")
        return {}
    with open(USER_DATA_FILE, 'r', encoding='utf-8') as file:
        return json.load(file)

def save_user_data(user_data):
    logger.info("Сохранение данных пользователей.")
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as file:
        json.dump(user_data, file, ensure_ascii=False, indent=4)

def add_user(user_id, username):
    user_data = load_user_data()
    user_data[user_id] = username
    save_user_data(user_data)

def get_user_count():
    user_data = load_user_data()
    return len(user_data)

