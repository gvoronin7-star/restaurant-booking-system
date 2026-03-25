"""
Модель столика ресторана.
"""

from typing import Optional


class TableModel:
    """
    Класс для работы со столиками ресторана.
    Реализует CRUD операции и управление доступностью.
    """
    
    # Допустимые значения
    VALID_STATUSES = ('available', 'occupied', 'reserved', 'maintenance')
    VALID_LOCATIONS = ('main_hall', 'terrace', 'vip_room', 'bar')
    
    def __init__(self, db_driver):
        """
        Инициализация модели.
        
        Args:
            db_driver: Экземпляр драйвера БД
        """
        self.db = db_driver
    
    def validate_capacity(self, capacity: int) -> bool:
        """Валидация вместимости столика."""
        return isinstance(capacity, int) and 1 <= capacity <= 20
    
    def validate_table_number(self, table_number: str) -> bool:
        """Валидация номера столика."""
        if not table_number:
            return False
        return len(table_number.strip()) <= 10
    
    def validate_status(self, status: str) -> bool:
        """Валидация статуса столика."""
        return status in self.VALID_STATUSES
    
    def validate_location(self, location: str) -> bool:
        """Валидация расположения столика."""
        return location in self.VALID_LOCATIONS
    
    def create(self, table_number: str, capacity: int, 
               location: str = 'main_hall', status: str = 'available') -> Optional[int]:
        """
        Создание нового столика.
        
        Args:
            table_number: Номер столика
            capacity: Вместимость (1-20)
            location: Расположение
            status: Статус
            
        Returns:
            ID созданного столика или None при ошибке
            
        Raises:
            ValueError: При некорректных данных
        """
        if not self.validate_table_number(table_number):
            raise ValueError("Номер столика не может быть пустым")
        if not self.validate_capacity(capacity):
            raise ValueError("Вместимость должна быть от 1 до 20")
        if not self.validate_location(location):
            raise ValueError(f"Недопустимое расположение. Допустимые: {', '.join(self.VALID_LOCATIONS)}")
        if not self.validate_status(status):
            raise ValueError(f"Недопустимый статус. Допустимые: {', '.join(self.VALID_STATUSES)}")
        
        table_number = table_number.strip().upper()
        
        # Проверка уникальности номера столика
        existing = self.get_by_number(table_number)
        if existing:
            raise ValueError(f"Столик с номером {table_number} уже существует")
        
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                """INSERT INTO tables (table_number, capacity, location, status) 
                   VALUES (%s, %s, %s, %s)""",
                (table_number, capacity, location, status)
            )
            cursor.execute("SELECT lastval() as id")
            result = cursor.fetchone()
            return result['id'] if result else None
    
    def get_by_id(self, table_id: int) -> Optional[dict]:
        """Получить столик по ID."""
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("SELECT * FROM tables WHERE id = %s", (table_id,))
            return cursor.fetchone()
    
    def get_by_number(self, table_number: str) -> Optional[dict]:
        """Получить столик по номеру."""
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                "SELECT * FROM tables WHERE table_number = %s", 
                (table_number.strip().upper(),)
            )
            return cursor.fetchone()
    
    def get_all(self) -> list[dict]:
        """Получить все столики."""
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("SELECT * FROM tables ORDER BY table_number")
            return cursor.fetchall()
    
    def get_available(self, date: str = None, time: str = None) -> list[dict]:
        """
        Получить доступные столики на указанное время.
        
        Args:
            date: Дата в формате YYYY-MM-DD
            time: Время в формате HH:MM
            
        Returns:
            Список доступных столиков
        """
        if not date or not time:
            # Просто возвращаем столики со статусом available
            with self.db._get_cursor(dict_cursor=True) as cursor:
                cursor.execute(
                    """SELECT * FROM tables 
                       WHERE status = 'available' 
                       ORDER BY capacity""")
                return cursor.fetchall()
        
        # Находим столики, которые НЕ забронированы на указанное время
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                """SELECT t.* FROM tables t
                   WHERE t.status = 'available'
                   AND t.id NOT IN (
                       SELECT b.table_id FROM bookings b
                       WHERE b.booking_date = %s
                       AND b.status IN ('confirmed', 'pending')
                       AND (
                           (b.start_time <= %s AND b.end_time > %s)
                           OR (b.start_time < %s AND b.end_time >= %s)
                           OR (b.start_time >= %s AND b.end_time <= %s)
                       )
                   )
                   ORDER BY t.capacity""",
                (date, time, time, time, time, time, time)
            )
            return cursor.fetchall()
    
    def get_by_capacity(self, min_capacity: int, max_capacity: int = None) -> list[dict]:
        """Получить столики по вместимости."""
        if max_capacity is None:
            max_capacity = min_capacity
        
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                """SELECT * FROM tables 
                   WHERE capacity >= %s AND capacity <= %s 
                   ORDER BY capacity""",
                (min_capacity, max_capacity)
            )
            return cursor.fetchall()
    
    def get_by_location(self, location: str) -> list[dict]:
        """Получить столики по расположению."""
        if not self.validate_location(location):
            raise ValueError(f"Недопустимое расположение")
        
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                "SELECT * FROM tables WHERE location = %s ORDER BY table_number",
                (location,)
            )
            return cursor.fetchall()
    
    def update_status(self, table_id: int, status: str) -> bool:
        """Обновить статус столика."""
        if not self.validate_status(status):
            raise ValueError(f"Недопустимый статус")
        
        with self.db._get_cursor() as cursor:
            cursor.execute(
                "UPDATE tables SET status = %s WHERE id = %s",
                (status, table_id)
            )
            return cursor.rowcount > 0
    
    def update(self, table_id: int, table_number: str = None,
               capacity: int = None, location: str = None,
               status: str = None) -> bool:
        """
        Обновить данные столика.
        
        Args:
            table_id: ID столика
            table_number: Новый номер (опционально)
            capacity: Новая вместимость (опционально)
            location: Новое расположение (опционально)
            status: Новый статус (опционально)
            
        Returns:
            True при успехе
        """
        updates = []
        params = []
        
        if table_number is not None:
            if not self.validate_table_number(table_number):
                raise ValueError("Номер столика не может быть пустым")
            updates.append("table_number = %s")
            params.append(table_number.strip().upper())
        
        if capacity is not None:
            if not self.validate_capacity(capacity):
                raise ValueError("Вместимость должна быть от 1 до 20")
            updates.append("capacity = %s")
            params.append(capacity)
        
        if location is not None:
            if not self.validate_location(location):
                raise ValueError(f"Недопустимое расположение")
            updates.append("location = %s")
            params.append(location)
        
        if status is not None:
            if not self.validate_status(status):
                raise ValueError(f"Недопустимый статус")
            updates.append("status = %s")
            params.append(status)
        
        if not updates:
            return False
        
        params.append(table_id)
        
        query = f"UPDATE tables SET {', '.join(updates)} WHERE id = %s"
        
        with self.db._get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount > 0
    
    def delete(self, table_id: int) -> bool:
        """Удалить столик."""
        with self.db._get_cursor() as cursor:
            cursor.execute("DELETE FROM tables WHERE id = %s", (table_id,))
            return cursor.rowcount > 0
    
    def get_availability_matrix(self, date: str) -> dict:
        """
        Получить матрицу доступности столиков на дату.
        
        Returns:
            Словарь: {table_id: {time: availability}}
        """
        with self.db._get_cursor(dict_cursor=True) as cursor:
            # Получаем все столики
            cursor.execute("SELECT id, table_number, capacity FROM tables ORDER BY table_number")
            tables = cursor.fetchall()
            
            # Получаем бронирования на дату
            cursor.execute(
                """SELECT table_id, start_time, end_time FROM bookings 
                   WHERE booking_date = %s AND status IN ('confirmed', 'pending')""",
                (date,)
            )
            bookings = cursor.fetchall()
            
            # Строим матрицу
            result = {}
            time_slots = [f"{h:02d}:00" for h in range(10, 23)]  # 10:00 - 22:00
            
            for table in tables:
                table_id = table['id']
                result[table['table_number']] = {
                    'capacity': table['capacity'],
                    'slots': {}
                }
                
                for slot in time_slots:
                    # Проверяем, есть ли бронь на это время
                    is_available = True
                    for booking in bookings:
                        if booking['table_id'] == table_id:
                            start = str(booking['start_time'])[:5]
                            end = str(booking['end_time'])[:5]
                            if start <= slot < end:
                                is_available = False
                                break
                    
                    result[table['table_number']]['slots'][slot] = is_available
            
            return result
