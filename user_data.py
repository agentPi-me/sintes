import os
import psycopg2
from psycopg2 import sql
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserDataManager:
    _instance = None
    _conn = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_db()
        return cls._instance

    def _initialize_db(self):
        try:
            # Используем DATABASE_URL из Heroku
            DATABASE_URL = os.environ.get('DATABASE_URL')
            if not DATABASE_URL:
                raise ValueError("DATABASE_URL не найден")
            
            # Для compatibility с Heroku Postgres
            if DATABASE_URL.startswith("postgres://"):
                DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")
            
            self._conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            
            with self._conn.cursor() as cur:
                # Создаем таблицу пользователей
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username TEXT,
                        start_count INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                self._conn.commit()
            
            logger.info("База данных инициализирована успешно")
        
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise

    def add_user(self, user_id: int, username: str):
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (user_id, username) 
                    VALUES (%s, %s) 
                    ON CONFLICT (user_id) DO NOTHING
                """, (user_id, username))
                self._conn.commit()
            logger.info(f"Добавлен пользователь: {user_id}")
        
        except Exception as e:
            logger.error(f"Ошибка при добавлении пользователя: {e}")
            self._conn.rollback()

    def get_user_count(self) -> int:
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users")
                return cur.fetchone()[0]
        
        except Exception as e:
            logger.error(f"Ошибка подсчета пользователей: {e}")
            return 0

    def add_start_count(self, user_id: int) -> bool:
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (user_id, start_count) 
                    VALUES (%s, 1) 
                    ON CONFLICT (user_id) 
                    DO UPDATE SET start_count = users.start_count + 1
                """, (user_id,))
                self._conn.commit()
                return True
        
        except Exception as e:
            logger.error(f"Ошибка подсчета стартов: {e}")
            self._conn.rollback()
            return False

    def get_unique_start_count(self) -> int:
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT COUNT(DISTINCT user_id) FROM users WHERE start_count > 0")
                return cur.fetchone()[0]
        
        except Exception as e:
            logger.error(f"Ошибка подсчета уникальных стартов: {e}")
            return 0

# Создаем синглтон
user_data_manager = UserDataManager()

# Функции для обратной совместимости
def add_user(user_id, username):
    user_data_manager.add_user(user_id, username)

def get_user_count():
    return user_data_manager.get_user_count()

def add_start_count(user_id):
    return user_data_manager.add_start_count(user_id)

def get_unique_start_count():
    return user_data_manager.get_unique_start_count()