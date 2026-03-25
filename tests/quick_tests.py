"""
Быстрые тесты валидации (без подключения к БД).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.client import ClientModel
from models.table import TableModel
from models.booking import BookingModel


def test_client_validation():
    """Тест валидации клиента."""
    print("Тест валидации клиента...")
    model = ClientModel(None)
    
    # Email
    assert model.validate_email("test@example.com") is True
    assert model.validate_email("invalid") is False
    assert model.validate_email("") is False
    
    # Phone
    assert model.validate_phone("+79001234567") is True
    assert model.validate_phone("89001234567") is True
    assert model.validate_phone("abc") is False
    
    # Name
    assert model.validate_name("Иван") is True
    assert model.validate_name("А") is False
    assert model.validate_name("") is False
    
    print("  ✓ Валидация клиента работает корректно")


def test_table_validation():
    """Тест валидации столика."""
    print("Тест валидации столика...")
    model = TableModel(None)
    
    # Capacity
    assert model.validate_capacity(1) is True
    assert model.validate_capacity(10) is True
    assert model.validate_capacity(20) is True
    assert model.validate_capacity(0) is False
    assert model.validate_capacity(21) is False
    
    # Status
    assert model.validate_status("available") is True
    assert model.validate_status("occupied") is True
    assert model.validate_status("invalid") is False
    
    # Location
    assert model.validate_location("main_hall") is True
    assert model.validate_location("terrace") is True
    assert model.validate_location("vip_room") is True
    assert model.validate_location("bar") is True
    assert model.validate_location("invalid") is False
    
    print("  ✓ Валидация столика работает корректно")


def test_booking_validation():
    """Тест валидации бронирования."""
    print("Тест валидации бронирования...")
    model = BookingModel(None)
    
    # Date
    from datetime import datetime, timedelta
    future = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    past = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    assert model.validate_date(future) is True
    assert model.validate_date(past) is False
    assert model.validate_date("invalid") is False
    
    # Time
    assert model.validate_time("10:00") is True
    assert model.validate_time("21:00") is True
    assert model.validate_time("09:00") is False
    assert model.validate_time("23:00") is False
    
    # Booking time
    assert model.validate_booking_time("10:00", "12:00") is True
    assert model.validate_booking_time("10:00", "10:30") is False  # Слишком коротко
    assert model.validate_booking_time("10:00", "15:00") is False  # Слишком долго
    
    # Status
    assert model.validate_status("pending") is True
    assert model.validate_status("confirmed") is True
    assert model.validate_status("cancelled") is True
    assert model.validate_status("completed") is True
    assert model.validate_status("no_show") is True
    assert model.validate_status("invalid") is False
    
    print("  ✓ Валидация бронирования работает корректно")


def test_imports():
    """Тест импортов."""
    print("Тест импортов...")
    
    from backend import RestaurantBackend
    from postgres_driver import DatabaseDriver
    
    print("  ✓ Все модули импортируются корректно")


def main():
    """Запуск всех быстрых тестов."""
    print("=" * 50)
    print("Быстрые тесты (без БД)")
    print("=" * 50)
    print()
    
    try:
        test_imports()
        test_client_validation()
        test_table_validation()
        test_booking_validation()
        
        print()
        print("=" * 50)
        print("✓ Все тесты пройдены успешно!")
        print("=" * 50)
        return 0
        
    except Exception as e:
        print()
        print("=" * 50)
        print(f"✗ Ошибка: {e}")
        print("=" * 50)
        return 1


if __name__ == "__main__":
    sys.exit(main())
