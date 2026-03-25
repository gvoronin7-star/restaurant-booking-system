"""
Модель клиента (посетителя ресторана).
"""

import re
from typing import Optional
from datetime import datetime


class ClientModel:
    """
    Класс для работы с клиентами ресторана.
    Реализует CRUD операции и валидацию данных.
    """
    
    # Паттерны для валидации
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')  # E.164 format
    
    def __init__(self, db_driver):
        """
        Инициализация модели.
        
        Args:
            db_driver: Экземпляр драйвера БД
        """
        self.db = db_driver
    
    def validate_email(self, email: str) -> bool:
        """Валидация email адреса."""
        if not email:
            return False
        return bool(self.EMAIL_PATTERN.match(email))
    
    def validate_phone(self, phone: str) -> bool:
        """Валидация номера телефона."""
        if not phone:
            return False
        # Удаляем пробелы и дефисы для проверки
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        return bool(self.PHONE_PATTERN.match(clean_phone))
    
    def validate_name(self, name: str) -> bool:
        """Валидация имени клиента."""
        if not name or len(name.strip()) < 2:
            return False
        return len(name.strip()) <= 100
    
    def create(self, name: str, email: str, phone: str) -> Optional[int]:
        """
        Создание нового клиента.
        
        Args:
            name: Имя клиента
            email: Email клиента
            phone: Телефон клиента
            
        Returns:
            ID созданного клиента или None при ошибке
            
        Raises:
            ValueError: При некорректных данных
        """
        # Валидация данных
        if not self.validate_name(name):
            raise ValueError("Имя должно содержать минимум 2 символа")
        if not self.validate_email(email):
            raise ValueError("Некорректный формат email")
        if not self.validate_phone(phone):
            raise ValueError("Некорректный формат телефона")
        
        name = name.strip()
        email = email.strip().lower()
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                """INSERT INTO clients (name, email, phone, created_at) 
                   VALUES (%s, %s, %s, %s)""",
                (name, email, phone, datetime.now())
            )
            cursor.execute("SELECT lastval() as id")
            result = cursor.fetchone()
            return result['id'] if result else None
    
    def get_by_id(self, client_id: int) -> Optional[dict]:
        """Получить клиента по ID."""
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
            return cursor.fetchone()
    
    def get_all(self) -> list[dict]:
        """Получить всех клиентов."""
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("SELECT * FROM clients ORDER BY name")
            return cursor.fetchall()
    
    def get_by_email(self, email: str) -> Optional[dict]:
        """Найти клиента по email."""
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                "SELECT * FROM clients WHERE email = %s", 
                (email.strip().lower(),)
            )
            return cursor.fetchone()
    
    def get_by_phone(self, phone: str) -> Optional[dict]:
        """Найти клиента по телефону."""
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                "SELECT * FROM clients WHERE phone = %s", 
                (clean_phone,)
            )
            return cursor.fetchone()
    
    def update(self, client_id: int, name: str = None, 
               email: str = None, phone: str = None) -> bool:
        """
        Обновить данные клиента.
        
        Args:
            client_id: ID клиента
            name: Новое имя (опционально)
            email: Новый email (опционально)
            phone: Новый телефон (опционально)
            
        Returns:
            True при успехе
        """
        updates = []
        params = []
        
        if name is not None:
            if not self.validate_name(name):
                raise ValueError("Имя должно содержать минимум 2 символа")
            updates.append("name = %s")
            params.append(name.strip())
        
        if email is not None:
            if not self.validate_email(email):
                raise ValueError("Некорректный формат email")
            updates.append("email = %s")
            params.append(email.strip().lower())
        
        if phone is not None:
            if not self.validate_phone(phone):
                raise ValueError("Некорректный формат телефона")
            updates.append("phone = %s")
            params.append(re.sub(r'[\s\-\(\)]', '', phone))
        
        if not updates:
            return False
        
        params.append(client_id)
        
        query = f"UPDATE clients SET {', '.join(updates)} WHERE id = %s"
        
        with self.db._get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount > 0
    
    def delete(self, client_id: int) -> bool:
        """Удалить клиента."""
        with self.db._get_cursor() as cursor:
            cursor.execute("DELETE FROM clients WHERE id = %s", (client_id,))
            return cursor.rowcount > 0
    
    def search(self, query: str) -> list[dict]:
        """Поиск клиентов по имени, email или телефону."""
        search_term = f"%{query.strip()}%"
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                """SELECT * FROM clients 
                   WHERE name LIKE %s OR email LIKE %s OR phone LIKE %s
                   ORDER BY name""",
                (search_term, search_term, search_term)
            )
            return cursor.fetchall()
