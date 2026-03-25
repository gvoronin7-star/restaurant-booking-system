"""
Бизнес-логика системы бронирования ресторана.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from postgres_driver import DatabaseDriver
from models import ClientModel, TableModel, BookingModel


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RestaurantBackend:
    """
    Основной класс бизнес-логики системы бронирования.
    Координирует работу всех моделей и обеспечивает транзакционность.
    """
    
    def __init__(self, db_driver: DatabaseDriver = None):
        """
        Инициализация backend.
        
        Args:
            db_driver: Драйвер БД (создаётся автоматически если не передан)
        """
        if db_driver is None:
            self.db = DatabaseDriver()
        else:
            self.db = db_driver
        
        # Инициализация моделей
        self.clients = ClientModel(self.db)
        self.tables = TableModel(self.db)
        self.bookings = BookingModel(self.db)
        
        logger.info("Backend инициализирован")
    
    def connect(self) -> bool:
        """Подключение к БД."""
        success = self.db.connect()
        if success:
            logger.info("Подключение к БД установлено")
        else:
            logger.error("Не удалось подключиться к БД")
        return success
    
    def disconnect(self):
        """Отключение от БД."""
        self.db.disconnect()
        logger.info("Подключение к БД закрыто")
    
    def initialize_database(self):
        """Создание таблиц БД (только если не существуют)."""
        logger.info("Создание таблиц БД...")
        
        with self.db._get_cursor(dict_cursor=True) as cursor:
            # Проверяем существуют ли таблицы
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM information_schema.tables 
                WHERE table_name IN ('clients', 'tables', 'bookings')
            """)
            result = cursor.fetchone()
            
            if result['cnt'] >= 3:
                logger.info("Таблицы уже существуют, пропускаем создание")
                return
            
            # Таблица клиентов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Таблица столиков
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tables (
                    id SERIAL PRIMARY KEY,
                    table_number TEXT UNIQUE NOT NULL,
                    capacity INT NOT NULL CHECK (capacity >= 1 AND capacity <= 20),
                    location TEXT NOT NULL DEFAULT 'main_hall',
                    status TEXT NOT NULL DEFAULT 'available' 
                        CHECK (status IN ('available', 'occupied', 'reserved', 'maintenance'))
                )
            """)
            
            # Таблица бронирований
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    id SERIAL PRIMARY KEY,
                    client_id INT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                    table_id INT NOT NULL REFERENCES tables(id) ON DELETE CASCADE,
                    booking_date DATE NOT NULL,
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    guest_count INT NOT NULL CHECK (guest_count >= 1),
                    notes TEXT DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'confirmed', 'cancelled', 'completed', 'no_show')),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    CONSTRAINT valid_time CHECK (start_time < end_time)
                )
            """)
            
            # Индексы для оптимизации (IGNORE - чтобы не报错 при повторном создании)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bookings_date ON bookings(booking_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bookings_table_date ON bookings(table_id, booking_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bookings_client ON bookings(client_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email)
            """)
        
        logger.info("Таблицы БД созданы успешно")
    
    def seed_demo_data(self):
        """Заполнение БД демо-данными (только если данных нет)."""
        logger.info("Заполнение демо-данными...")
        
        # Проверяем есть ли уже клиенты
        existing_clients = self.clients.get_all()
        if existing_clients:
            logger.info("Демо-данные уже существуют, пропускаем")
            return
        
        # Создаём клиентов
        clients = [
            ("Иван Иванов", "ivan@example.com", "+79001234567"),
            ("Мария Петрова", "maria@example.com", "+79002345678"),
            ("Алексей Сидоров", "alex@example.com", "+79003456789"),
            ("Елена Смирнова", "elena@example.com", "+79004567890"),
            ("Дмитрий Козлов", "dmitry@example.com", "+79005678901"),
        ]
        
        client_ids = []
        for name, email, phone in clients:
            try:
                cid = self.clients.create(name, email, phone)
                client_ids.append(cid)
                logger.info(f"Создан клиент: {name}")
            except Exception as e:
                logger.warning(f"Не удалось создать клиента {name}: {e}")
        
        # Создаём столики
        tables = [
            ("A1", 2, "main_hall"),
            ("A2", 4, "main_hall"),
            ("A3", 6, "main_hall"),
            ("B1", 2, "terrace"),
            ("B2", 4, "terrace"),
            ("C1", 8, "vip_room"),
            ("D1", 2, "bar"),
            ("D2", 2, "bar"),
        ]
        
        table_ids = []
        for number, capacity, location in tables:
            try:
                tid = self.tables.create(number, capacity, location)
                table_ids.append(tid)
                logger.info(f"Создан столик: {number}")
            except Exception as e:
                logger.warning(f"Не удалось создать столик {number}: {e}")
        
        # Создаём бронирования
        today = datetime.now().date()
        
        bookings = [
            (client_ids[0], table_ids[1], today + timedelta(days=1), "18:00", "20:00", 3),
            (client_ids[1], table_ids[2], today + timedelta(days=1), "19:00", "22:00", 5),
            (client_ids[2], table_ids[4], today + timedelta(days=2), "12:00", "14:00", 4),
            (client_ids[3], table_ids[5], today + timedelta(days=2), "19:00", "22:00", 7, "День рождения"),
            (client_ids[4], table_ids[0], today + timedelta(days=3), "13:00", "15:00", 2),
        ]
        
        for booking_data in bookings:
            try:
                client_id, table_id, date, start, end, guests = booking_data[:6]
                notes = booking_data[6] if len(booking_data) > 6 else ""
                
                bid = self.bookings.create(
                    client_id, table_id, 
                    date.strftime("%Y-%m-%d"), 
                    start, end, guests, notes, "confirmed"
                )
                logger.info(f"Создано бронирование #{bid}")
            except Exception as e:
                logger.warning(f"Не удалось создать бронирование: {e}")
        
        logger.info("Демо-данные загружены")
    
    # === Высокоуровневые операции ===
    
    def quick_book(self, client_name: str, client_email: str, client_phone: str,
                   guest_count: int, date: str, start_time: str, 
                   duration_hours: int = 2) -> dict:
        """
        Быстрое бронирование - создаёт клиента и бронь за один вызов.
        
        Args:
            client_name: Имя клиента
            client_email: Email
            client_phone: Телефон
            guest_count: Количество гостей
            date: Дата (YYYY-MM-DD)
            start_time: Время начала (HH:MM)
            duration_hours: Продолжительность в часах
            
        Returns:
            Словарь с информацией о созданном бронировании
        """
        logger.info(f"Быстрое бронирование: {client_name}, {guest_count} гостей, {date} {start_time}")
        
        # Пробуем найти существующего клиента
        client = self.clients.get_by_email(client_email)
        
        if not client:
            # Создаём нового клиента
            client_id = self.clients.create(client_name, client_email, client_phone)
            client = self.clients.get_by_id(client_id)
        else:
            client_id = client['id']
        
        # Вычисляем время окончания
        start_dt = datetime.strptime(start_time, "%H:%M")
        end_dt = start_dt + timedelta(hours=duration_hours)
        end_time = end_dt.strftime("%H:%M")
        
        # Находим доступный столик
        available_tables = self.tables.get_available(date, start_time)
        
        # Фильтруем по вместимости
        suitable_tables = [t for t in available_tables if t['capacity'] >= guest_count]
        
        if not suitable_tables:
            raise ValueError("Нет доступных столиков на указанное время")
        
        # Берём первый подходящий столик
        table = suitable_tables[0]
        
        # Создаём бронирование
        booking_id = self.bookings.create(
            client_id=client_id,
            table_id=table['id'],
            date=date,
            start_time=start_time,
            end_time=end_time,
            guest_count=guest_count,
            status="confirmed"
        )
        
        logger.info(f"Бронирование создано: #{booking_id}")
        
        return {
            "booking_id": booking_id,
            "client": client,
            "table": table,
            "date": date,
            "time": f"{start_time} - {end_time}",
            "guests": guest_count
        }
    
    def get_daily_schedule(self, date: str) -> list[dict]:
        """
        Получить расписание на день.
        
        Args:
            date: Дата (YYYY-MM-DD)
            
        Returns:
            Список бронирований с информацией о клиентах и столиках
        """
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(
                """SELECT 
                       b.id, b.booking_date, b.start_time, b.end_time,
                       b.guest_count, b.status, b.notes,
                       t.table_number, t.location,
                       c.name as client_name, c.phone as client_phone
                   FROM bookings b
                   JOIN tables t ON b.table_id = t.id
                   JOIN clients c ON b.client_id = c.id
                   WHERE b.booking_date = %s
                   ORDER BY b.start_time""",
                (date,)
            )
            return cursor.fetchall()
    
    def find_table_for_group(self, guest_count: int, date: str, 
                            start_time: str, end_time: str) -> Optional[dict]:
        """
        Найти подходящий столик для группы.
        
        Args:
            guest_count: Количество гостей
            date: Дата
            start_time: Время начала
            end_time: Время окончания
            
        Returns:
            Информация о столике или None
        """
        # Получаем все доступные столики
        available = self.tables.get_available(date, start_time)
        
        # Сортируем по вместимости (находим минимально подходящий)
        suitable = [t for t in available if t['capacity'] >= guest_count]
        
        if not suitable:
            return None
        
        # Проверяем доступность для точного временного диапазона
        for table in suitable:
            if self.bookings.check_availability(
                table['id'], date, start_time, end_time
            ):
                return table
        
        return None
    
    def cancel_booking_with_notification(self, booking_id: int) -> bool:
        """
        Отменить бронирование с логированием.
        
        Args:
            booking_id: ID бронирования
            
        Returns:
            True при успехе
        """
        booking = self.bookings.get_by_id(booking_id)
        if not booking:
            logger.warning(f"Бронирование #{booking_id} не найдено")
            return False
        
        success = self.bookings.cancel(booking_id)
        
        if success:
            logger.info(
                f"Бронирование #{booking_id} отменено. "
                f"Клиент: {booking['client_name']}, "
                f"Столик: {booking['table_number']}"
            )
        
        return success
    
    def auto_complete_past_bookings(self) -> int:
        """
        Автоматически отметить прошедшие бронирования как завершённые.
        
        Returns:
            Количество обработанных бронирований
        """
        today = datetime.now().date()
        current_time = datetime.now().time()
        
        with self.db._get_cursor() as cursor:
            cursor.execute(
                """UPDATE bookings 
                   SET status = 'completed', updated_at = %s
                   WHERE booking_date < %s
                   AND status IN ('confirmed', 'pending')""",
                (datetime.now(), today)
            )
            count = cursor.rowcount
            
            # Также отмечаем прошедшие сегодняшние
            cursor.execute(
                """UPDATE bookings 
                   SET status = 'completed', updated_at = %s
                   WHERE booking_date = %s
                   AND end_time < %s
                   AND status IN ('confirmed', 'pending')""",
                (datetime.now(), today, current_time)
            )
            count += cursor.rowcount
        
        if count > 0:
            logger.info(f"Автоматически завершено {count} бронирований")
        
        return count
    
    def __enter__(self):
        """Контекстный менеджер - вход."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход."""
        self.disconnect()
