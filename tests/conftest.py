"""
Конфигурация pytest для тестов.
"""

import os
import sys
import pytest
from datetime import datetime, timedelta

# Настройка пути для импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_test_db_config():
    """Конфигурация для тестовой БД."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "database": os.getenv("DB_NAME", "testdb"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "")
    }


@pytest.fixture(scope="session")
def db_config():
    """Фикстура конфигурации БД."""
    return get_test_db_config()


@pytest.fixture
def test_date():
    """Фикстура тестовой даты (завтра)."""
    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")


@pytest.fixture
def test_time():
    """Фикстура тестового времени."""
    return "19:00"


@pytest.fixture
def sample_client_data():
    """Фикстура данных тестового клиента."""
    return {
        "name": "Тестовый Клиент",
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "phone": "+79001234567"
    }


@pytest.fixture
def sample_table_data():
    """Фикстура данных тестового столика."""
    return {
        "table_number": f"TEST-{datetime.now().second}",
        "capacity": 4,
        "location": "main_hall"
    }
