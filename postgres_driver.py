"""
PostgreSQL Database Driver с поддержкой транзакций.
"""

import os
import sys
import io

# Настройка UTF-8 для Windows (только при запуске из терминала)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'buffer'):
            import codecs
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Any, Optional
from dotenv import load_dotenv

load_dotenv()


class DatabaseDriver:
    """
    Класс для работы с PostgreSQL.
    """
    
    def __init__(self, config: Optional[dict] = None):
        if config:
            self.config = config
        else:
            self.config = {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", 5432)),
                "database": os.getenv("DB_NAME", "testdb"),
                "user": os.getenv("DB_USER", "postgres"),
                "password": os.getenv("DB_PASSWORD", "")
            }
        self._connection = None
    
    def connect(self) -> bool:
        try:
            self._connection = psycopg2.connect(**self.config)
            return True
        except psycopg2.OperationalError as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    def disconnect(self):
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def is_connected(self) -> bool:
        return self._connection is not None and not self._connection.closed
    
    @contextmanager
    def _get_cursor(self, dict_cursor: bool = False):
        """Контекстный менеджер для курсора с автокоммитом."""
        if not self.is_connected():
            if not self.connect():
                raise ConnectionError("Не удалось подключиться к БД")
        
        cursor = self._connection.cursor(
            cursor_factory=RealDictCursor if dict_cursor else None
        )
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def create_tables(self):
        """Создание таблиц users и orders (с автоинкрементом)."""
        with self._get_cursor(dict_cursor=True) as cursor:
            # Создаем новые таблицы с правильным SERIAL
            cursor.execute("DROP TABLE IF EXISTS users_new CASCADE")
            cursor.execute("DROP TABLE IF EXISTS orders_new CASCADE")
            
            cursor.execute("""
                CREATE TABLE users_new (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INT CHECK (age >= 0)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE orders_new (
                    id SERIAL PRIMARY KEY,
                    user_id INT NOT NULL REFERENCES users_new(id) ON DELETE CASCADE,
                    amount NUMERIC(10,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
                
        print("Таблицы созданы")
    
    def clear_tables(self):
        """Очистка таблиц."""
        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM orders_new")
            cursor.execute("DELETE FROM users_new")
        print("Таблицы очищены")
    
    def add_user(self, name: str, age: int) -> Optional[int]:
        """
        Добавление пользователя.
        Использует параметризованный запрос.
        """
        with self._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                "INSERT INTO users_new (name, age) VALUES (%s, %s)",
                (name, age)
            )
            # Получаем последний сгенерированный ID
            cursor.execute("SELECT lastval() as id")
            result = cursor.fetchone()
            return result['id'] if result else None
    
    def add_order(self, user_id: int, amount: float) -> Optional[int]:
        """
        Добавление заказа.
        Использует параметризованный запрос.
        """
        with self._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                "INSERT INTO orders_new (user_id, amount) VALUES (%s, %s)",
                (user_id, amount)
            )
            # Получаем последний сгенерированный ID
            cursor.execute("SELECT lastval() as id")
            result = cursor.fetchone()
            return result['id'] if result else None
    
    def get_user_totals(self) -> list[dict]:
        """
        Агрегирующий запрос: сумма заказов по каждому пользователю.
        LEFT JOIN + SUM + GROUP BY + ORDER BY
        """
        with self._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("""
                SELECT 
                    u.id,
                    u.name,
                    COALESCE(SUM(o.amount), 0) AS total_amount
                FROM users_new u
                LEFT JOIN orders_new o ON o.user_id = u.id
                GROUP BY u.id, u.name
                ORDER BY total_amount DESC
            """)
            return cursor.fetchall()
    
    def get_all_users(self) -> list[dict]:
        """Получить всех пользователей."""
        with self._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("SELECT * FROM users_new ORDER BY id")
            return cursor.fetchall()
    
    def get_all_orders(self) -> list[dict]:
        """Получить все заказы."""
        with self._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("SELECT * FROM orders_new ORDER BY id")
            return cursor.fetchall()
    
    def delete_user(self, user_id: int) -> int:
        """Удаление пользователя (проверка CASCADE)."""
        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM users_new WHERE id = %s", (user_id,))
            return cursor.rowcount
    
    def query(self, query: str, params: Optional[tuple] = None) -> Any:
        """Выполнение произвольного запроса."""
        with self._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(query, params or ())
            if query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            return cursor.rowcount
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
