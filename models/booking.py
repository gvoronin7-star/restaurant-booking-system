"""
Модель бронирования столика.
"""

from datetime import datetime, timedelta
from typing import Optional
import re


class BookingModel:
    """
    Класс для работы с бронированиями.
    Реализует CRUD операции, проверку доступности и управление статусами.
    """
    
    # Допустимые статусы бронирования
    VALID_STATUSES = ('pending', 'confirmed', 'cancelled', 'completed', 'no_show')
    
    # Временные границы работы ресторана
    RESTAURANT_OPEN = 10  # 10:00
    RESTAURANT_CLOSE = 22  # 22:00
    MIN_BOOKING_DURATION = 1  # час
    MAX_BOOKING_DURATION = 4  # часа
    
    def __init__(self, db_driver):
        """
        Инициализация модели.
        
        Args:
            db_driver: Экземпляр драйвера БД
        """
        self.db = db_driver
    
    def validate_date(self, date_str: str) -> bool:
        """Валидация даты (YYYY-MM-DD)."""
        if not date_str:
            return False
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            # Нельзя бронировать на прошедшие даты
            return date >= datetime.now().date()
        except ValueError:
            return False
    
    def validate_time(self, time_str: str) -> bool:
        """Валидация времени (HH:MM)."""
        if not time_str:
            return False
        try:
            time = datetime.strptime(time_str, '%H:%M').time()
            return self.RESTAURANT_OPEN <= time.hour < self.RESTAURANT_CLOSE
        except ValueError:
            return False
    
    def validate_status(self, status: str) -> bool:
        """Валидация статуса бронирования."""
        return status in self.VALID_STATUSES
    
    def validate_booking_time(self, start_time: str, end_time: str) -> bool:
        """Валидация времени бронирования."""
        try:
            start = datetime.strptime(start_time, '%H:%M')
            end = datetime.strptime(end_time, '%H:%M')
            
            duration = (end - start).total_seconds() / 3600
            
            return (self.MIN_BOOKING_DURATION <= duration <= self.MAX_BOOKING_DURATION and
                    start.hour >= self.RESTAURANT_OPEN and
                    end.hour <= self.RESTAURANT_CLOSE)
        except ValueError:
            return False
    
    def check_availability(self, table_id: int, date: str, 
                          start_time: str, end_time: str,
                          exclude_booking_id: int = None) -> bool:
        """
        Проверка доступности столика на указанное время.
        
        Args:
            table_id: ID столика
            date: Дата (YYYY-MM-DD)
            start_time: Время начала (HH:MM)
            end_time: Время окончания (HH:MM)
            exclude_booking_id: ID брони для исключения (при обновлении)
            
        Returns:
            True если столик доступен
        """
        # Проверяем, что столик существует и доступен
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                "SELECT status FROM tables WHERE id = %s", 
                (table_id,)
            )
            table = cursor.fetchone()
            
            if not table or table['status'] != 'available':
                return False
            
            # Проверяем пересечения с существующими бронированиями
            query = """
                SELECT id FROM bookings 
                WHERE table_id = %s 
                AND booking_date = %s 
                AND status IN ('confirmed', 'pending')
                AND (
                    (start_time < %s AND end_time > %s)
                    OR (start_time < %s AND end_time > %s)
                    OR (start_time >= %s AND end_time <= %s)
                )
            """
            params = (table_id, date, end_time, start_time, end_time, start_time, start_time, end_time)
            
            if exclude_booking_id:
                query += " AND id != %s"
                params = params + (exclude_booking_id,)
            
            cursor.execute(query, params)
            conflicts = cursor.fetchall()
            
            return len(conflicts) == 0
    
    def get_conflicts(self, table_id: int, date: str,
                     start_time: str, end_time: str) -> list[dict]:
        """
        Получить конфликтующие бронирования.
        
        Args:
            table_id: ID столика
            date: Дата (YYYY-MM-DD)
            start_time: Время начала
            end_time: Время окончания
            
        Returns:
            Список конфликтующих бронирований
        """
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                """SELECT b.*, t.table_number, c.name as client_name
                   FROM bookings b
                   JOIN tables t ON b.table_id = t.id
                   JOIN clients c ON b.client_id = c.id
                   WHERE b.table_id = %s 
                   AND b.booking_date = %s 
                   AND b.status IN ('confirmed', 'pending')
                   AND (
                       (b.start_time < %s AND b.end_time > %s)
                       OR (b.start_time < %s AND b.end_time > %s)
                       OR (b.start_time >= %s AND b.end_time <= %s)
                   )
                   ORDER BY b.start_time""",
                (table_id, date, end_time, start_time, end_time, start_time, start_time, end_time)
            )
            return cursor.fetchall()
    
    def create(self, client_id: int, table_id: int, date: str,
               start_time: str, end_time: str, 
               guest_count: int = 1, notes: str = '',
               status: str = 'pending') -> Optional[int]:
        """
        Создание бронирования.
        
        Args:
            client_id: ID клиента
            table_id: ID столика
            date: Дата (YYYY-MM-DD)
            start_time: Время начала (HH:MM)
            end_time: Время окончания (HH:MM)
            guest_count: Количество гостей
            notes: Заметки
            status: Статус бронирования
            
        Returns:
            ID созданного бронирования
            
        Raises:
            ValueError: При некорректных данных или конфликте
        """
        # Валидация
        if not self.validate_date(date):
            raise ValueError("Некорректная дата или дата в прошлом")
        if not self.validate_time(start_time):
            raise ValueError(f"Время должно быть между {self.RESTAURANT_OPEN}:00 и {self.RESTAURANT_CLOSE-1}:00")
        if not self.validate_booking_time(start_time, end_time):
            raise ValueError(f"Длительность бронирования должна быть от {self.MIN_BOOKING_DURATION} до {self.MAX_BOOKING_DURATION} часов")
        if not self.validate_status(status):
            raise ValueError(f"Недопустимый статус: {status}")
        if not isinstance(guest_count, int) or guest_count < 1:
            raise ValueError("Количество гостей должно быть >= 1")
        
        # Проверка доступности
        if not self.check_availability(table_id, date, start_time, end_time):
            conflicts = self.get_conflicts(table_id, date, start_time, end_time)
            if conflicts:
                conflict = conflicts[0]
                raise ValueError(
                    f"Столик занят с {conflict['start_time']} до {conflict['end_time']}"
                )
            raise ValueError("Столик недоступен")
        
        # Проверка вместимости столика
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("SELECT capacity FROM tables WHERE id = %s", (table_id,))
            table = cursor.fetchone()
            if table and table['capacity'] < guest_count:
                raise ValueError(f"Столик вмещает только {table['capacity']} гостей")
        
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                """INSERT INTO bookings 
                   (client_id, table_id, booking_date, start_time, end_time, 
                    guest_count, notes, status, created_at) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (client_id, table_id, date, start_time, end_time, 
                 guest_count, notes, status, datetime.now())
            )
            cursor.execute("SELECT lastval() as id")
            result = cursor.fetchone()
            return result['id'] if result else None
    
    def get_by_id(self, booking_id: int) -> Optional[dict]:
        """Получить бронирование по ID."""
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                """SELECT b.*, t.table_number, c.name as client_name, 
                          c.phone as client_phone, c.email as client_email
                   FROM bookings b
                   JOIN tables t ON b.table_id = t.id
                   JOIN clients c ON b.client_id = c.id
                   WHERE b.id = %s""", 
                (booking_id,)
            )
            return cursor.fetchone()
    
    def get_all(self, status: str = None) -> list[dict]:
        """Получить все бронирования."""
        with self.db._get_cursor(dict_cursor=True) as cursor:
            if status:
                cursor.execute(
                    """SELECT b.*, t.table_number, c.name as client_name
                       FROM bookings b
                       JOIN tables t ON b.table_id = t.id
                       JOIN clients c ON b.client_id = c.id
                       WHERE b.status = %s
                       ORDER BY b.booking_date, b.start_time""",
                    (status,)
                )
            else:
                cursor.execute(
                    """SELECT b.*, t.table_number, c.name as client_name
                       FROM bookings b
                       JOIN tables t ON b.table_id = t.id
                       JOIN clients c ON b.client_id = c.id
                       ORDER BY b.booking_date, b.start_time"""
                )
            return cursor.fetchall()
    
    def get_by_client(self, client_id: int) -> list[dict]:
        """Получить бронирования клиента."""
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                """SELECT b.*, t.table_number
                   FROM bookings b
                   JOIN tables t ON b.table_id = t.id
                   WHERE b.client_id = %s
                   ORDER BY b.booking_date DESC, b.start_time""",
                (client_id,)
            )
            return cursor.fetchall()
    
    def get_by_table(self, table_id: int, date: str = None) -> list[dict]:
        """Получить бронирования столика."""
        with self.db._get_cursor(dict_cursor=True) as cursor:
            if date:
                cursor.execute(
                    """SELECT b.*, c.name as client_name
                       FROM bookings b
                       JOIN clients c ON b.client_id = c.id
                       WHERE b.table_id = %s AND b.booking_date = %s
                       AND b.status IN ('confirmed', 'pending')
                       ORDER BY b.start_time""",
                    (table_id, date)
                )
            else:
                cursor.execute(
                    """SELECT b.*, c.name as client_name
                       FROM bookings b
                       JOIN clients c ON b.client_id = c.id
                       WHERE b.table_id = %s
                       AND b.status IN ('confirmed', 'pending')
                       ORDER BY b.booking_date, b.start_time""",
                    (table_id,)
                )
            return cursor.fetchall()
    
    def get_by_date(self, date: str) -> list[dict]:
        """Получить все бронирования на дату."""
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                """SELECT b.*, t.table_number, c.name as client_name
                   FROM bookings b
                   JOIN tables t ON b.table_id = t.id
                   JOIN clients c ON b.client_id = c.id
                   WHERE b.booking_date = %s
                   ORDER BY b.start_time""",
                (date,)
            )
            return cursor.fetchall()
    
    def get_upcoming(self, limit: int = 10) -> list[dict]:
        """Получить предстоящие бронирования."""
        today = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M')
        
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                """SELECT b.*, t.table_number, c.name as client_name
                   FROM bookings b
                   JOIN tables t ON b.table_id = t.id
                   JOIN clients c ON b.client_id = c.id
                   WHERE b.booking_date >= %s
                   AND b.status IN ('confirmed', 'pending')
                   AND (b.booking_date > %s OR b.start_time >= %s)
                   ORDER BY b.booking_date, b.start_time
                   LIMIT %s""",
                (today, today, current_time, limit)
            )
            return cursor.fetchall()
    
    def update_status(self, booking_id: int, status: str) -> bool:
        """Обновить статус бронирования."""
        if not self.validate_status(status):
            raise ValueError(f"Недопустимый статус")
        
        with self.db._get_cursor() as cursor:
            cursor.execute(
                "UPDATE bookings SET status = %s, updated_at = %s WHERE id = %s",
                (status, datetime.now(), booking_id)
            )
            return cursor.rowcount > 0
    
    def update(self, booking_id: int, table_id: int = None,
               date: str = None, start_time: str = None,
               end_time: str = None, guest_count: int = None,
               notes: str = None) -> bool:
        """
        Обновить бронирование.
        
        Args:
            booking_id: ID бронирования
            table_id: Новый столик
            date: Новая дата
            start_time: Новое время начала
            end_time: Новое время окончания
            guest_count: Новое количество гостей
            notes: Новые заметки
            
        Returns:
            True при успехе
        """
        # Получаем текущее бронирование
        current = self.get_by_id(booking_id)
        if not current:
            return False
        
        # Используем переданные значения или текущие
        new_table_id = table_id if table_id else current['table_id']
        new_date = date if date else str(current['booking_date'])
        new_start = start_time if start_time else str(current['start_time'])[:5]
        new_end = end_time if end_time else str(current['end_time'])[:5]
        new_guests = guest_count if guest_count else current['guest_count']
        
        # Валидация
        if date and not self.validate_date(date):
            raise ValueError("Некорректная дата")
        if start_time and not self.validate_time(start_time):
            raise ValueError("Некорректное время начала")
        if end_time and not self.validate_time(end_time):
            raise ValueError("Некорректное время окончания")
        if not self.validate_booking_time(new_start, new_end):
            raise ValueError("Некорректная длительность бронирования")
        
        # Проверка доступности при изменении времени/столика
        if (table_id and table_id != current['table_id']) or \
           date or start_time or end_time:
            if not self.check_availability(new_table_id, new_date, 
                                          new_start, new_end, booking_id):
                raise ValueError("Столик недоступен на указанное время")
        
        # Проверка вместимости
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("SELECT capacity FROM tables WHERE id = %s", (new_table_id,))
            table = cursor.fetchone()
            if table and table['capacity'] < new_guests:
                raise ValueError(f"Столик вмещает только {table['capacity']} гостей")
        
        updates = []
        params = []
        
        if table_id is not None:
            updates.append("table_id = %s")
            params.append(table_id)
        if date is not None:
            updates.append("booking_date = %s")
            params.append(date)
        if start_time is not None:
            updates.append("start_time = %s")
            params.append(start_time)
        if end_time is not None:
            updates.append("end_time = %s")
            params.append(end_time)
        if guest_count is not None:
            updates.append("guest_count = %s")
            params.append(guest_count)
        if notes is not None:
            updates.append("notes = %s")
            params.append(notes)
        
        if not updates:
            return False
        
        updates.append("updated_at = %s")
        params.append(datetime.now())
        
        params.append(booking_id)
        
        query = f"UPDATE bookings SET {', '.join(updates)} WHERE id = %s"
        
        with self.db._get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount > 0
    
    def cancel(self, booking_id: int) -> bool:
        """Отменить бронирование."""
        return self.update_status(booking_id, 'cancelled')
    
    def confirm(self, booking_id: int) -> bool:
        """Подтвердить бронирование."""
        return self.update_status(booking_id, 'confirmed')
    
    def complete(self, booking_id: int) -> bool:
        """Отметить бронирование как завершённое."""
        return self.update_status(booking_id, 'completed')
    
    def mark_no_show(self, booking_id: int) -> bool:
        """Отметить как неявку."""
        return self.update_status(booking_id, 'no_show')
    
    def delete(self, booking_id: int) -> bool:
        """Удалить бронирование."""
        with self.db._get_cursor() as cursor:
            cursor.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
            return cursor.rowcount > 0
    
    def get_daily_summary(self, date: str) -> dict:
        """Получить сводку на день."""
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                """SELECT 
                       COUNT(*) as total_bookings,
                       SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) as confirmed,
                       SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                       SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                       SUM(guest_count) as total_guests
                   FROM bookings 
                   WHERE booking_date = %s""",
                (date,)
            )
            return cursor.fetchone()
    
    def get_statistics(self, start_date: str, end_date: str) -> dict:
        """Получить статистику за период."""
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                """SELECT 
                       COUNT(*) as total_bookings,
                       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                       SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                       SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) as no_shows,
                       AVG(guest_count) as avg_guests
                   FROM bookings 
                   WHERE booking_date BETWEEN %s AND %s""",
                (start_date, end_date)
            )
            return cursor.fetchone()
