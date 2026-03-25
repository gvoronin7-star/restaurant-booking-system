"""
Тесты для модели бронирования (BookingModel).
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from postgres_driver import DatabaseDriver
from models.booking import BookingModel


class TestBookingValidation:
    """Тесты валидации данных бронирования."""
    
    def test_validate_date_valid(self):
        """Тест валидации корректной даты."""
        model = BookingModel(None)
        future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        assert model.validate_date(future_date) is True
    
    def test_validate_date_past(self):
        """Тест валидации прошедшей даты."""
        model = BookingModel(None)
        past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        assert model.validate_date(past_date) is False
    
    def test_validate_date_invalid(self):
        """Тест валидации некорректной даты."""
        model = BookingModel(None)
        assert model.validate_date("") is False
        assert model.validate_date("invalid") is False
        assert model.validate_date("2024-13-45") is False
    
    def test_validate_time_valid(self):
        """Тест валидации корректного времени."""
        model = BookingModel(None)
        assert model.validate_time("10:00") is True
        assert model.validate_time("21:00") is True
    
    def test_validate_time_invalid(self):
        """Тест валидации некорректного времени."""
        model = BookingModel(None)
        assert model.validate_time("") is False
        assert model.validate_time("invalid") is False
        assert model.validate_time("09:00") is False  # До открытия
        assert model.validate_time("23:00") is False  # После закрытия
    
    def test_validate_booking_time_valid(self):
        """Тест валидации времени бронирования."""
        model = BookingModel(None)
        assert model.validate_booking_time("10:00", "12:00") is True
        assert model.validate_booking_time("19:00", "22:00") is True
    
    def test_validate_booking_time_too_short(self):
        """Тест слишком короткого бронирования."""
        model = BookingModel(None)
        assert model.validate_booking_time("10:00", "10:30") is False
    
    def test_validate_booking_time_too_long(self):
        """Тест слишком длинного бронирования."""
        model = BookingModel(None)
        assert model.validate_booking_time("10:00", "15:00") is False
    
    def test_validate_status_valid(self):
        """Тест валидации статуса."""
        model = BookingModel(None)
        assert model.validate_status("pending") is True
        assert model.validate_status("confirmed") is True
        assert model.validate_status("cancelled") is True
        assert model.validate_status("completed") is True
        assert model.validate_status("no_show") is True
    
    def test_validate_status_invalid(self):
        """Тест валидации некорректного статуса."""
        model = BookingModel(None)
        assert model.validate_status("invalid") is False


class TestBookingCRUD:
    """Тесты CRUD операций бронирования."""
    
    @pytest.fixture
    def db_driver(self):
        """Фикстура драйвера БД."""
        driver = DatabaseDriver()
        driver.connect()
        
        with driver._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("DROP TABLE IF EXISTS bookings CASCADE")
            cursor.execute("DROP TABLE IF EXISTS tables CASCADE")
            cursor.execute("DROP TABLE IF EXISTS clients CASCADE")
            
            cursor.execute("""
                CREATE TABLE clients (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            cursor.execute("""
                CREATE TABLE tables (
                    id SERIAL PRIMARY KEY,
                    table_number TEXT UNIQUE NOT NULL,
                    capacity INT NOT NULL,
                    location TEXT NOT NULL DEFAULT 'main_hall',
                    status TEXT NOT NULL DEFAULT 'available'
                )
            """)
            
            cursor.execute("""
                CREATE TABLE bookings (
                    id SERIAL PRIMARY KEY,
                    client_id INT NOT NULL,
                    table_id INT NOT NULL,
                    booking_date DATE NOT NULL,
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    guest_count INT NOT NULL,
                    notes TEXT DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
        
        yield driver
        
        with driver._get_cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS bookings CASCADE")
            cursor.execute("DROP TABLE IF EXISTS tables CASCADE")
            cursor.execute("DROP TABLE IF EXISTS clients CASCADE")
        driver.disconnect()
    
    @pytest.fixture
    def booking_model(self, db_driver):
        """Фикстура модели бронирования."""
        return BookingModel(db_driver)
    
    @pytest.fixture
    def setup_test_data(self, db_driver, booking_model):
        """Фикстура тестовых данных (клиент и столик)."""
        # Создаем клиента
        with db_driver._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("""
                INSERT INTO clients (name, email, phone)
                VALUES ('Test Client', 'test@example.com', '+79001234567')
                RETURNING id
            """)
            client_id = cursor.fetchone()['id']
            
            cursor.execute("""
                INSERT INTO tables (table_number, capacity, location, status)
                VALUES ('TEST1', 4, 'main_hall', 'available'),
                       ('TEST2', 6, 'main_hall', 'available')
                RETURNING id
            """)
            tables = cursor.fetchall()
            table1_id = tables[0]['id']
            table2_id = tables[1]['id']
        
        return {
            'client_id': client_id,
            'table1_id': table1_id,
            'table2_id': table2_id
        }
    
    def test_create_booking(self, booking_model, setup_test_data, test_date):
        """Тест создания бронирования."""
        booking_id = booking_model.create(
            client_id=setup_test_data['client_id'],
            table_id=setup_test_data['table1_id'],
            date=test_date,
            start_time="19:00",
            end_time="21:00",
            guest_count=3,
            status="confirmed"
        )
        
        assert booking_id is not None
        assert isinstance(booking_id, int)
    
    def test_create_booking_past_date(self, booking_model, setup_test_data):
        """Тест создания бронирования на прошедшую дату."""
        past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        with pytest.raises(ValueError, match="Некорректная дата"):
            booking_model.create(
                client_id=setup_test_data['client_id'],
                table_id=setup_test_data['table1_id'],
                date=past_date,
                start_time="19:00",
                end_time="21:00",
                guest_count=3
            )
    
    def test_create_booking_invalid_time(self, booking_model, setup_test_data, test_date):
        """Тест создания бронирования на некорректное время."""
        with pytest.raises(ValueError, match="Время должно быть между"):
            booking_model.create(
                client_id=setup_test_data['client_id'],
                table_id=setup_test_data['table1_id'],
                date=test_date,
                start_time="09:00",  # До открытия
                end_time="11:00",
                guest_count=3
            )
    
    def test_create_booking_too_long(self, booking_model, setup_test_data, test_date):
        """Тест создания слишком длинного бронирования."""
        with pytest.raises(ValueError, match="Длительность бронирования"):
            booking_model.create(
                client_id=setup_test_data['client_id'],
                table_id=setup_test_data['table1_id'],
                date=test_date,
                start_time="10:00",
                end_time="15:00",  # 5 часов - слишком долго
                guest_count=3
            )
    
    def test_create_booking_guests_exceed_capacity(self, booking_model, setup_test_data, test_date):
        """Тест создания бронирования с превышением вместимости."""
        with pytest.raises(ValueError, match="вместит только"):
            booking_model.create(
                client_id=setup_test_data['client_id'],
                table_id=setup_test_data['table1_id'],  # Вместимость 4
                date=test_date,
                start_time="19:00",
                end_time="21:00",
                guest_count=10  # Больше чем 4
            )
    
    def test_get_by_id(self, booking_model, setup_test_data, test_date):
        """Тест получения бронирования по ID."""
        booking_id = booking_model.create(
            client_id=setup_test_data['client_id'],
            table_id=setup_test_data['table1_id'],
            date=test_date,
            start_time="19:00",
            end_time="21:00",
            guest_count=3
        )
        
        booking = booking_model.get_by_id(booking_id)
        
        assert booking is not None
        assert booking['guest_count'] == 3
    
    def test_get_all(self, booking_model, setup_test_data, test_date):
        """Тест получения всех бронирований."""
        booking_model.create(
            client_id=setup_test_data['client_id'],
            table_id=setup_test_data['table1_id'],
            date=test_date,
            start_time="19:00",
            end_time="21:00",
            guest_count=3
        )
        
        bookings = booking_model.get_all()
        assert len(bookings) > 0
    
    def test_get_by_date(self, booking_model, setup_test_data, test_date):
        """Тест получения бронирований на дату."""
        booking_model.create(
            client_id=setup_test_data['client_id'],
            table_id=setup_test_data['table1_id'],
            date=test_date,
            start_time="19:00",
            end_time="21:00",
            guest_count=3
        )
        
        bookings = booking_model.get_by_date(test_date)
        assert len(bookings) > 0
    
    def test_update_status(self, booking_model, setup_test_data, test_date):
        """Тест обновления статуса."""
        booking_id = booking_model.create(
            client_id=setup_test_data['client_id'],
            table_id=setup_test_data['table1_id'],
            date=test_date,
            start_time="19:00",
            end_time="21:00",
            guest_count=3,
            status="pending"
        )
        
        success = booking_model.update_status(booking_id, "confirmed")
        assert success is True
        
        booking = booking_model.get_by_id(booking_id)
        assert booking['status'] == "confirmed"
    
    def test_cancel_booking(self, booking_model, setup_test_data, test_date):
        """Тест отмены бронирования."""
        booking_id = booking_model.create(
            client_id=setup_test_data['client_id'],
            table_id=setup_test_data['table1_id'],
            date=test_date,
            start_time="19:00",
            end_time="21:00",
            guest_count=3
        )
        
        success = booking_model.cancel(booking_id)
        assert success is True
        
        booking = booking_model.get_by_id(booking_id)
        assert booking['status'] == "cancelled"
    
    def test_confirm_booking(self, booking_model, setup_test_data, test_date):
        """Тест подтверждения бронирования."""
        booking_id = booking_model.create(
            client_id=setup_test_data['client_id'],
            table_id=setup_test_data['table1_id'],
            date=test_date,
            start_time="19:00",
            end_time="21:00",
            guest_count=3,
            status="pending"
        )
        
        success = booking_model.confirm(booking_id)
        assert success is True
    
    def test_complete_booking(self, booking_model, setup_test_data, test_date):
        """Тест завершения бронирования."""
        booking_id = booking_model.create(
            client_id=setup_test_data['client_id'],
            table_id=setup_test_data['table1_id'],
            date=test_date,
            start_time="19:00",
            end_time="21:00",
            guest_count=3,
            status="confirmed"
        )
        
        success = booking_model.complete(booking_id)
        assert success is True
    
    def test_delete_booking(self, booking_model, setup_test_data, test_date):
        """Тест удаления бронирования."""
        booking_id = booking_model.create(
            client_id=setup_test_data['client_id'],
            table_id=setup_test_data['table1_id'],
            date=test_date,
            start_time="19:00",
            end_time="21:00",
            guest_count=3
        )
        
        success = booking_model.delete(booking_id)
        assert success is True
        
        booking = booking_model.get_by_id(booking_id)
        assert booking is None


class TestBookingConflicts:
    """Тесты конфликтов бронирований."""
    
    @pytest.fixture
    def db_driver(self):
        """Фикстура драйвера БД."""
        driver = DatabaseDriver()
        driver.connect()
        
        with driver._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("DROP TABLE IF EXISTS bookings CASCADE")
            cursor.execute("DROP TABLE IF EXISTS tables CASCADE")
            cursor.execute("DROP TABLE IF EXISTS clients CASCADE")
            
            cursor.execute("""
                CREATE TABLE clients (id SERIAL PRIMARY KEY, name TEXT, email TEXT, phone TEXT)
            """)
            cursor.execute("""
                CREATE TABLE tables (id SERIAL PRIMARY KEY, table_number TEXT, capacity INT, status TEXT)
            """)
            cursor.execute("""
                CREATE TABLE bookings (
                    id SERIAL PRIMARY KEY, client_id INT, table_id INT, booking_date DATE,
                    start_time TIME, end_time TIME, guest_count INT, status TEXT
                )
            """)
        
        yield driver
        
        with driver._get_cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS bookings CASCADE")
            cursor.execute("DROP TABLE IF EXISTS tables CASCADE")
            cursor.execute("DROP TABLE IF EXISTS clients CASCADE")
        driver.disconnect()
    
    @pytest.fixture
    def setup_data(self, db_driver):
        """Фикстура тестовых данных."""
        with db_driver._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("INSERT INTO clients (name, email, phone) VALUES ('Test', 'test@test.com', '+7900') RETURNING id")
            client_id = cursor.fetchone()['id']
            
            cursor.execute("INSERT INTO tables (table_number, capacity, status) VALUES ('T1', 4, 'available') RETURNING id")
            table_id = cursor.fetchone()['id']
        
        return {'client_id': client_id, 'table_id': table_id}
    
    @pytest.fixture
    def booking_model(self, db_driver):
        """Фикстура модели бронирования."""
        return BookingModel(db_driver)
    
    def test_check_availability_no_conflict(self, booking_model, setup_data, test_date):
        """Тест доступности без конфликта."""
        is_available = booking_model.check_availability(
            setup_data['table_id'], test_date, "14:00", "16:00"
        )
        assert is_available is True
    
    def test_check_availability_with_existing_booking(self, booking_model, setup_data, test_date):
        """Тест доступности с существующим бронированием."""
        # Создаем бронирование на 19:00-21:00
        booking_model.create(
            client_id=setup_data['client_id'],
            table_id=setup_data['table_id'],
            date=test_date,
            start_time="19:00",
            end_time="21:00",
            guest_count=3,
            status="confirmed"
        )
        
        # Проверяем пересекающееся время
        is_available = booking_model.check_availability(
            setup_data['table_id'], test_date, "19:30", "21:30"
        )
        assert is_available is False
    
    def test_check_availability_non_overlapping(self, booking_model, setup_data, test_date):
        """Тест доступности без пересечения."""
        # Создаем бронирование на 19:00-21:00
        booking_model.create(
            client_id=setup_data['client_id'],
            table_id=setup_data['table_id'],
            date=test_date,
            start_time="19:00",
            end_time="21:00",
            guest_count=3,
            status="confirmed"
        )
        
        # Проверяем непересекающееся время
        is_available = booking_model.check_availability(
            setup_data['table_id'], test_date, "14:00", "16:00"
        )
        assert is_available is True
    
    def test_create_booking_conflict(self, booking_model, setup_data, test_date):
        """Тест создания бронирования с конфликтом."""
        # Создаем первое бронирование
        booking_model.create(
            client_id=setup_data['client_id'],
            table_id=setup_data['table_id'],
            date=test_date,
            start_time="19:00",
            end_time="21:00",
            guest_count=3,
            status="confirmed"
        )
        
        # Попытка создать пересекающееся бронирование
        with pytest.raises(ValueError, match="занят"):
            booking_model.create(
                client_id=setup_data['client_id'],
                table_id=setup_data['table_id'],
                date=test_date,
                start_time="20:00",  # Пересекается
                end_time="22:00",
                guest_count=3
            )
    
    def test_get_conflicts(self, booking_model, setup_data, test_date):
        """Тест получения конфликтующих бронирований."""
        # Создаем бронирование
        booking_id = booking_model.create(
            client_id=setup_data['client_id'],
            table_id=setup_data['table_id'],
            date=test_date,
            start_time="19:00",
            end_time="21:00",
            guest_count=3,
            status="confirmed"
        )
        
        # Получаем конфликты
        conflicts = booking_model.get_conflicts(
            setup_data['table_id'], test_date, "20:00", "22:00"
        )
        
        assert len(conflicts) > 0
        assert conflicts[0]['id'] == booking_id


class TestBookingStatistics:
    """Тесты статистики бронирований."""
    
    @pytest.fixture
    def db_driver(self):
        """Фикстура драйвера БД."""
        driver = DatabaseDriver()
        driver.connect()
        
        with driver._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("DROP TABLE IF EXISTS bookings CASCADE")
            cursor.execute("DROP TABLE IF EXISTS tables CASCADE")
            cursor.execute("DROP TABLE IF EXISTS clients CASCADE")
            
            cursor.execute("""
                CREATE TABLE clients (id SERIAL PRIMARY KEY, name TEXT, email TEXT, phone TEXT)
            """)
            cursor.execute("""
                CREATE TABLE tables (id SERIAL PRIMARY KEY, table_number TEXT, capacity INT, status TEXT)
            """)
            cursor.execute("""
                CREATE TABLE bookings (
                    id SERIAL PRIMARY KEY, client_id INT, table_id INT, booking_date DATE,
                    start_time TIME, end_time TIME, guest_count INT, status TEXT
                )
            """)
        
        yield driver
        
        with driver._get_cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS bookings CASCADE")
            cursor.execute("DROP TABLE IF EXISTS tables CASCADE")
            cursor.execute("DROP TABLE IF EXISTS clients CASCADE")
        driver.disconnect()
    
    @pytest.fixture
    def setup_data(self, db_driver):
        """Фикстура тестовых данных."""
        with db_driver._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("INSERT INTO clients (name, email, phone) VALUES ('Test', 'test@test.com', '+7900') RETURNING id")
            client_id = cursor.fetchone()['id']
            
            cursor.execute("INSERT INTO tables (table_number, capacity, status) VALUES ('T1', 4, 'available') RETURNING id")
            table_id = cursor.fetchone()['id']
        
        return {'client_id': client_id, 'table_id': table_id}
    
    @pytest.fixture
    def booking_model(self, db_driver):
        """Фикстура модели бронирования."""
        return BookingModel(db_driver)
    
    def test_get_daily_summary(self, booking_model, setup_data, test_date):
        """Тест дневной сводки."""
        # Создаем несколько бронирований
        booking_model.create(
            client_id=setup_data['client_id'],
            table_id=setup_data['table_id'],
            date=test_date,
            start_time="19:00",
            end_time="21:00",
            guest_count=4,
            status="confirmed"
        )
        
        booking_model.create(
            client_id=setup_data['client_id'],
            table_id=setup_data['table_id'],
            date=test_date,
            start_time="14:00",
            end_time="16:00",
            guest_count=2,
            status="pending"
        )
        
        summary = booking_model.get_daily_summary(test_date)
        
        assert summary['total_bookings'] == 2
        assert summary['confirmed'] == 1
        assert summary['pending'] == 1
        assert summary['total_guests'] == 6
    
    def test_get_statistics(self, booking_model, setup_data):
        """Тест статистики за период."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        booking_model.create(
            client_id=setup_data['client_id'],
            table_id=setup_data['table_id'],
            date=today,
            start_time="19:00",
            end_time="21:00",
            guest_count=4,
            status="completed"
        )
        
        stats = booking_model.get_statistics(today, today)
        
        assert stats['total_bookings'] >= 1
        assert stats['completed'] >= 1
