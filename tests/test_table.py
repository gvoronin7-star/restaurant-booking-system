"""
Тесты для модели столика (TableModel).
"""

import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from postgres_driver import DatabaseDriver
from models.table import TableModel


class TestTableValidation:
    """Тесты валидации данных столика."""
    
    def test_validate_capacity_valid(self):
        """Тест валидации корректной вместимости."""
        model = TableModel(None)
        assert model.validate_capacity(1) is True
        assert model.validate_capacity(10) is True
        assert model.validate_capacity(20) is True
    
    def test_validate_capacity_invalid(self):
        """Тест валидации некорректной вместимости."""
        model = TableModel(None)
        assert model.validate_capacity(0) is False
        assert model.validate_capacity(-1) is False
        assert model.validate_capacity(21) is False
        assert model.validate_capacity("4") is False  # Не int
    
    def test_validate_table_number_valid(self):
        """Тест валидации номера столика."""
        model = TableModel(None)
        assert model.validate_table_number("A1") is True
        assert model.validate_table_number("VIP-1") is True
        assert model.validate_table_number("123") is True
    
    def test_validate_table_number_invalid(self):
        """Тест валидации некорректного номера столика."""
        model = TableModel(None)
        assert model.validate_table_number("") is False
        assert model.validate_table_number("   ") is False
    
    def test_validate_status_valid(self):
        """Тест валидации статуса."""
        model = TableModel(None)
        assert model.validate_status("available") is True
        assert model.validate_status("occupied") is True
        assert model.validate_status("reserved") is True
        assert model.validate_status("maintenance") is True
    
    def test_validate_status_invalid(self):
        """Тест валидации некорректного статуса."""
        model = TableModel(None)
        assert model.validate_status("invalid") is False
        assert model.validate_status("") is False
    
    def test_validate_location_valid(self):
        """Тест валидации локации."""
        model = TableModel(None)
        assert model.validate_location("main_hall") is True
        assert model.validate_location("terrace") is True
        assert model.validate_location("vip_room") is True
        assert model.validate_location("bar") is True
    
    def test_validate_location_invalid(self):
        """Тест валидации некорректной локации."""
        model = TableModel(None)
        assert model.validate_location("invalid") is False
        assert model.validate_location("") is False


class TestTableCRUD:
    """Тесты CRUD операций столика."""
    
    @pytest.fixture
    def db_driver(self):
        """Фикстура драйвера БД."""
        driver = DatabaseDriver()
        driver.connect()
        
        with driver._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("DROP TABLE IF EXISTS tables CASCADE")
            cursor.execute("DROP TABLE IF EXISTS bookings CASCADE")
            cursor.execute("""
                CREATE TABLE tables (
                    id SERIAL PRIMARY KEY,
                    table_number TEXT UNIQUE NOT NULL,
                    capacity INT NOT NULL CHECK (capacity >= 1 AND capacity <= 20),
                    location TEXT NOT NULL DEFAULT 'main_hall',
                    status TEXT NOT NULL DEFAULT 'available'
                )
            """)
        
        yield driver
        
        with driver._get_cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS tables CASCADE")
            cursor.execute("DROP TABLE IF EXISTS bookings CASCADE")
        driver.disconnect()
    
    @pytest.fixture
    def table_model(self, db_driver):
        """Фикстура модели столика."""
        return TableModel(db_driver)
    
    def test_create_table(self, table_model, sample_table_data):
        """Тест создания столика."""
        table_id = table_model.create(**sample_table_data)
        
        assert table_id is not None
        assert isinstance(table_id, int)
        assert table_id > 0
    
    def test_create_table_invalid_capacity(self, table_model, sample_table_data):
        """Тест создания столика с некорректной вместимостью."""
        sample_table_data["capacity"] = 25
        
        with pytest.raises(ValueError, match="Вместимость должна быть"):
            table_model.create(**sample_table_data)
    
    def test_create_table_invalid_location(self, table_model, sample_table_data):
        """Тест создания столика с некорректной локацией."""
        sample_table_data["location"] = "invalid"
        
        with pytest.raises(ValueError, match="Недопустимое расположение"):
            table_model.create(**sample_table_data)
    
    def test_create_table_duplicate_number(self, table_model, sample_table_data):
        """Тест создания столика с дублирующимся номером."""
        table_model.create(**sample_table_data)
        
        with pytest.raises(ValueError, match="уже существует"):
            table_model.create(**sample_table_data)
    
    def test_get_by_id(self, table_model, sample_table_data):
        """Тест получения столика по ID."""
        table_id = table_model.create(**sample_table_data)
        table = table_model.get_by_id(table_id)
        
        assert table is not None
        assert table['table_number'] == sample_table_data['table_number']
        assert table['capacity'] == sample_table_data['capacity']
    
    def test_get_by_number(self, table_model, sample_table_data):
        """Тест получения столика по номеру."""
        table_model.create(**sample_table_data)
        table = table_model.get_by_number(sample_table_data['table_number'])
        
        assert table is not None
        assert table['capacity'] == sample_table_data['capacity']
    
    def test_get_all(self, table_model, sample_table_data):
        """Тест получения всех столиков."""
        table_model.create(**sample_table_data)
        tables = table_model.get_all()
        
        assert len(tables) > 0
    
    def test_get_by_location(self, table_model, sample_table_data):
        """Тест получения столиков по локации."""
        table_model.create(**sample_table_data)
        tables = table_model.get_by_location("main_hall")
        
        assert len(tables) > 0
        
        tables = table_model.get_by_location("vip_room")
        assert len(tables) == 0
    
    def test_get_by_capacity(self, table_model, sample_table_data):
        """Тест получения столиков по вместимости."""
        table_model.create(**sample_table_data)
        tables = table_model.get_by_capacity(2, 6)
        
        assert all(2 <= t['capacity'] <= 6 for t in tables)
    
    def test_update_status(self, table_model, sample_table_data):
        """Тест обновления статуса столика."""
        table_id = table_model.create(**sample_table_data)
        
        success = table_model.update_status(table_id, "occupied")
        assert success is True
        
        table = table_model.get_by_id(table_id)
        assert table['status'] == "occupied"
    
    def test_update(self, table_model, sample_table_data):
        """Тест обновления столика."""
        table_id = table_model.create(**sample_table_data)
        
        success = table_model.update(table_id, capacity=8, status="reserved")
        assert success is True
        
        table = table_model.get_by_id(table_id)
        assert table['capacity'] == 8
        assert table['status'] == "reserved"
    
    def test_delete_table(self, table_model, sample_table_data):
        """Тест удаления столика."""
        table_id = table_model.create(**sample_table_data)
        
        success = table_model.delete(table_id)
        assert success is True
        
        table = table_model.get_by_id(table_id)
        assert table is None


class TestTableAvailability:
    """Тесты проверки доступности столиков."""
    
    @pytest.fixture
    def db_driver(self):
        """Фикстура драйвера БД."""
        driver = DatabaseDriver()
        driver.connect()
        
        with driver._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("DROP TABLE IF EXISTS tables CASCADE")
            cursor.execute("DROP TABLE IF EXISTS bookings CASCADE")
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
                    status TEXT NOT NULL DEFAULT 'confirmed'
                )
            """)
        
        yield driver
        
        with driver._get_cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS tables CASCADE")
            cursor.execute("DROP TABLE IF EXISTS bookings CASCADE")
        driver.disconnect()
    
    @pytest.fixture
    def table_model(self, db_driver):
        """Фикстура модели столика."""
        return TableModel(db_driver)
    
    @pytest.fixture
    def setup_data(self, db_driver, table_model):
        """Фикстура тестовых данных."""
        # Создаем столики
        table_model.create("T1", 4, "main_hall")
        table_model.create("T2", 6, "main_hall")
        
        # Создаем бронирование на столик T1
        with db_driver._get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO bookings (client_id, table_id, booking_date, start_time, end_time, guest_count, status)
                VALUES (1, 1, %s, '19:00', '21:00', 4, 'confirmed')
            """, ((datetime.now() + __import__('datetime').timedelta(days=1)).strftime("%Y-%m-%d"),))
    
    def test_get_available_with_bookings(self, table_model, setup_data, test_date, test_time):
        """Тест получения доступных столиков с учетом бронирований."""
        available = table_model.get_available(test_date, test_time)
        
        # Столик T1 занят в 19:00-21:00, T2 свободен
        table_numbers = [t['table_number'] for t in available]
        assert "T2" in table_numbers
    
    def test_get_available_no_conflict(self, table_model, setup_data, test_date):
        """Тест получения доступных столиков без конфликта."""
        # Запрашиваем время, когда нет бронирований
        available = table_model.get_available(test_date, "14:00")
        
        table_numbers = [t['table_number'] for t in available]
        assert "T1" in table_numbers
        assert "T2" in table_numbers
    
    def test_get_availability_matrix(self, table_model, setup_data, test_date):
        """Тест матрицы доступности."""
        matrix = table_model.get_availability_matrix(test_date)
        
        assert "T1" in matrix
        assert "T2" in matrix
        assert "slots" in matrix["T1"]
