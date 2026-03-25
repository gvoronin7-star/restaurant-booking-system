"""
Database Driver - модуль для работы с PostgreSQL.
Использование:
    from database import DatabaseDriver
    
    db = DatabaseDriver()
    db.connect()
"""

import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor, execute_batch
from contextlib import contextmanager
from typing import Any, Optional
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()


class DatabaseDriver:
    """
    Класс-драйвер для работы с PostgreSQL.
    Предоставляет методы для выполнения CRUD-операций.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Инициализация драйвера.
        
        Args:
            config: словарь с параметрами подключения. 
                   Если не передан - читается из переменных окружения.
        """
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
        """
        Установка подключения к базе данных.
        
        Returns:
            True если подключение успешно, иначе False.
        """
        try:
            self._connection = psycopg2.connect(**self.config)
            return True
        except psycopg2.OperationalError as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    def disconnect(self):
        """Закрытие подключения к базе данных."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def is_connected(self) -> bool:
        """Проверка состояния подключения."""
        return self._connection is not None and not self._connection.closed
    
    @contextmanager
    def _get_cursor(self, dict_cursor: bool = False):
        """
        Контекстный менеджер для получения курсора.
        
        Args:
            dict_cursor: если True - возвращает словарь вместо кортежа.
        """
        if not self.is_connected():
            if not self.connect():
                raise ConnectionError("Не удалось подключиться к базе данных")
        
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
    
    # ==================== CREATE ====================
    
    def insert(self, table: str, data: dict, return_id: bool = False) -> Optional[int]:
        """
        Вставка записи в таблицу.
        
        Args:
            table: имя таблицы.
            data: словарь с данными {колонка: значение}.
            return_id: возвращать ли ID (работает только для автоинкрементных полей).
            
        Returns:
            ID вставленной записи или None.
        """
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ["%s"] * len(columns)
        
        query_str = f"""
            INSERT INTO {table} ({', '.join(columns)}) 
            VALUES ({', '.join(placeholders)}) 
        """
        
        with self._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(query_str, values)
            
            if return_id:
                try:
                    # Пробуем получить последний ID
                    cursor.execute("SELECT lastval() as id")
                    result = cursor.fetchone()
                    return result['id'] if result else None
                except:
                    return None
            return None
    
    def insert_many(self, table: str, data: list[dict]) -> int:
        """
        Вставка нескольких записей.
        
        Args:
            table: имя таблицы.
            data: список словарей с данными.
            
        Returns:
            Количество вставленных записей.
        """
        if not data:
            return 0
        
        columns = list(data[0].keys())
        values_list = [list(row.values()) for row in data]
        placeholders = ["%s"] * len(columns)
        
        query_str = f"""
            INSERT INTO {table} ({', '.join(columns)}) 
            VALUES ({', '.join(placeholders)})
        """
        
        with self._get_cursor() as cursor:
            for values in values_list:
                cursor.execute(query_str, values)
            return len(data)
    
    # ==================== READ ====================
    
    def select_one(self, table: str, where: dict, columns: str = "*") -> Optional[dict]:
        """
        Получение одной записи.
        
        Args:
            table: имя таблицы.
            where: словарь условий {колонка: значение}.
            columns: список колонок через запятую или '*'.
            
        Returns:
            Словарь с данными или None.
        """
        columns_str = columns if isinstance(columns, str) else ", ".join(columns)
        
        where_parts = [sql.SQL("{} = {}").format(
            sql.Identifier(k), sql.Literal(v)
        ) for k, v in where.items()]
        where_str = sql.SQL(" AND ").join(where_parts)
        
        query = sql.SQL("SELECT {} FROM {} WHERE {} LIMIT 1").format(
            sql.SQL(columns_str),
            sql.Identifier(table),
            where_str
        )
        
        with self._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(query)
            return cursor.fetchone()
    
    def select_all(self, table: str, where: Optional[dict] = None, 
                   columns: str = "*", order_by: Optional[str] = None,
                   limit: Optional[int] = None) -> list[dict]:
        """
        Получение всех записей.
        
        Args:
            table: имя таблицы.
            where: словарь условий (опционально).
            columns: список колонок или '*'.
            order_by: поле для сортировки (опционально).
            limit: ограничение количества записей (опционально).
            
        Returns:
            Список словарей с данными.
        """
        columns_str = columns if isinstance(columns, str) else ", ".join(columns)
        
        query = sql.SQL("SELECT {} FROM {}").format(
            sql.SQL(columns_str),
            sql.Identifier(table)
        )
        
        if where:
            where_parts = [sql.SQL("{} = {}").format(
                sql.Identifier(k), sql.Literal(v)
            ) for k, v in where.items()]
            where_str = sql.SQL(" AND ").join(where_parts)
            query = sql.SQL("{} WHERE {}").format(query, where_str)
        
        if order_by:
            query = sql.SQL("{} ORDER BY {}").format(query, sql.Identifier(order_by))
        
        if limit:
            query = sql.SQL("{} LIMIT {}").format(query, sql.Literal(limit))
        
        with self._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(query)
            return cursor.fetchall()
    
    def query(self, query: str, params: Optional[tuple] = None, 
              fetch_one: bool = False, dict_cursor: bool = True) -> Any:
        """
        Выполнение произвольного SQL-запроса.
        
        Args:
            query: SQL-запрос.
            params: параметры запроса.
            fetch_one: получить одну запись.
            dict_cursor: использовать словарь вместо кортежа.
            
        Returns:
            Результат запроса.
        """
        with self._get_cursor(dict_cursor=dict_cursor) as cursor:
            cursor.execute(query, params or ())
            
            # Для SELECT возвращаем результат
            if query.strip().upper().startswith("SELECT"):
                if fetch_one:
                    return cursor.fetchone()
                return cursor.fetchall()
            
            # Для INSERT/UPDATE/DELETE возвращаем количество затронутых строк
            return cursor.rowcount
    
    # ==================== UPDATE ====================
    
    def update(self, table: str, data: dict, where: dict) -> int:
        """
        Обновление записей.
        
        Args:
            table: имя таблицы.
            data: словарь с новыми данными {колонка: значение}.
            where: словарь условий {колонка: значение}.
            
        Returns:
            Количество обновленных записей.
        """
        set_parts = [sql.SQL("{} = {}").format(
            sql.Identifier(k), sql.Literal(v)
        ) for k, v in data.items()]
        
        where_parts = [sql.SQL("{} = {}").format(
            sql.Identifier(k), sql.Literal(v)
        ) for k, v in where.items()]
        
        query = sql.SQL("UPDATE {} SET {} WHERE {}").format(
            sql.Identifier(table),
            sql.SQL(", ").join(set_parts),
            sql.SQL(" AND ").join(where_parts)
        )
        
        with self._get_cursor() as cursor:
            cursor.execute(query)
            return cursor.rowcount
    
    # ==================== DELETE ====================
    
    def delete(self, table: str, where: dict) -> int:
        """
        Удаление записей.
        
        Args:
            table: имя таблицы.
            where: словарь условий {колонка: значение}.
            
        Returns:
            Количество удаленных записей.
        """
        where_parts = [sql.SQL("{} = {}").format(
            sql.Identifier(k), sql.Literal(v)
        ) for k, v in where.items()]
        
        query = sql.SQL("DELETE FROM {} WHERE {}").format(
            sql.Identifier(table),
            sql.SQL(" AND ").join(where_parts)
        )
        
        with self._get_cursor() as cursor:
            cursor.execute(query)
            return cursor.rowcount
    
    def delete_by_id(self, table: str, id: int) -> bool:
        """
        Удаление записи по ID.
        
        Args:
            table: имя таблицы.
            id: ID записи.
            
        Returns:
            True если удалено, иначе False.
        """
        rows = self.delete(table, {"id": id})
        return rows > 0
    
    # ==================== UTILITY ====================
    
    def exists(self, table: str, where: dict) -> bool:
        """
        Проверка существования записи.
        
        Args:
            table: имя таблицы.
            where: словарь условий.
            
        Returns:
            True если запись существует.
        """
        result = self.select_one(table, where, columns="1")
        return result is not None
    
    def count(self, table: str, where: Optional[dict] = None) -> int:
        """
        Подсчет количества записей.
        
        Args:
            table: имя таблицы.
            where: словарь условий (опционально).
            
        Returns:
            Количество записей.
        """
        query = sql.SQL("SELECT COUNT(*) as cnt FROM {}").format(
            sql.Identifier(table)
        )
        
        if where:
            where_parts = [sql.SQL("{} = {}").format(
                sql.Identifier(k), sql.Literal(v)
            ) for k, v in where.items()]
            where_str = sql.SQL(" AND ").join(where_parts)
            query = sql.SQL("{} WHERE {}").format(query, where_str)
        
        with self._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(query)
            return cursor.fetchone()['cnt']
    
    def get_version(self) -> str:
        """Получение версии PostgreSQL."""
        with self._get_cursor() as cursor:
            cursor.execute("SELECT version();")
            return cursor.fetchone()[0]
    
    def __enter__(self):
        """Вход в контекстный менеджер."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера."""
        self.disconnect()
