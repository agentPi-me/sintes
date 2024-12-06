import json
import os
import logging
from typing import Dict, Any

USER_DATA_FILE = 'user_data.json'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserDataManager:
    _instance = None
    _user_data: Dict[str, Any] = {}

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def load_user_data(cls) -> Dict[str, Any]:
        """Загрузка данных пользователей с singleton-подходом."""
        if not cls._user_data:
            try:
                if os.path.exists(USER_DATA_FILE):
                    with open(USER_DATA_FILE, 'r', encoding='utf-8') as file:
                        cls._user_data = json.load(file)
            except Exception as e:
                logger.error(f"Ошибка при загрузке данных пользователей: {e}")
                cls._user_data = {}
        return cls._user_data

    @classmethod
    def save_user_data(cls, user_data: Dict[str, Any] = None):
        """Сохранение данных пользователей."""
        data = user_data or cls._user_data
        try:
            with open(USER_DATA_FILE, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            logger.info("Данные пользователей сохранены.")
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных пользователей: {e}")

    @classmethod
    def add_user(cls, user_id: int, username: str):
        """Добавление нового пользователя."""
        user_data = cls.load_user_data()
        user_id_str = str(user_id)

        if user_id_str not in user_data.get('users', {}):
            if 'users' not in user_data:
                user_data['users'] = {}

            user_data['users'][user_id_str] = username
            cls.save_user_data(user_data)
            logger.info(f"Добавлен новый пользователь: {user_id}")

    @classmethod
    def get_user_count(cls) -> int:
        """Получение количества пользователей."""
        user_data = cls.load_user_data()
        return len(user_data.get('users', {}))

    @classmethod
    def add_start_count(cls, user_id: int) -> bool:
        """Подсчет количества нажатий /start."""
        user_data = cls.load_user_data()
        user_id_str = str(user_id)

        if 'start_count' not in user_data:
            user_data['start_count'] = {}

        if user_id_str not in user_data['start_count']:
            user_data['start_count'][user_id_str] = 1
            cls.save_user_data(user_data)
            return True

        return False

    @classmethod
    def get_unique_start_count(cls) -> int:
        """Получение количества уникальных нажатий /start."""
        user_data = cls.load_user_data()
        return len(user_data.get('start_count', {}))

user_data_manager = UserDataManager()

def load_user_data():
    return user_data_manager.load_user_data()

def save_user_data(user_data):
    user_data_manager.save_user_data(user_data)

def add_user(user_id, username):
    user_data_manager.add_user(user_id, username)

def get_user_count():
    return user_data_manager.get_user_count()

def add_start_count(user_id):
    return user_data_manager.add_start_count(user_id)

def get_unique_start_count():
    return user_data_manager.get_unique_start_count()