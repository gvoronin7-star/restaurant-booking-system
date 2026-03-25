"""
Тесты для модели клиента (ClientModel).
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from postgres_driver import DatabaseDriver
from models.client import ClientModel


class TestClientValidation:
    """Тесты валидации данных клиента."""
    
    def test_validate_email_valid(self):
        """Тест валидации корректного email."""
        model = ClientModel(None)
        assert model.validate_email("test@example.com") is True
        assert model.validate_email("user.name@domain.co.uk") is True
    
    def test_validate_email_invalid(self):
        """Тест валидации некорректного email."""
        model = ClientModel(None)
        assert model.validate_email("") is False
        assert model.validate_email("invalid") is False
        assert model.validate_email("@example.com") is False
        assert model.validate_email("test@") is False
    
    def test_validate_phone_valid(self):
        """Тест валидации корректного телефона."""
        model = ClientModel(None)
        assert model.validate_phone("+79001234567") is True
        assert model.validate_phone("89001234567") is True
        assert model.validate_phone("+7 900 123 45 67") is True
    
    def test_validate_phone_invalid(self):
        """Тест валидации некорректного телефона."""
        model = ClientModel(None)
        assert model.validate_phone("") is False
        assert model.validate_phone("abc") is False
        assert model.validate_phone("+") is False
    
    def test_validate_name_valid(self):
        """Тест валидации корректного имени."""
        model = ClientModel(None)
        assert model.validate_name("Иван") is True
        assert model.validate_name("А") is False  # Минимум 2 символа
        assert model.validate_name("А" * 100) is True  # Ровно 100
        assert model.validate_name("А" * 101) is False  # Больше 100
    
    def test_validate_name_invalid(self):
        """Тест валидации некорректного имени."""
        model = ClientModel(None)
        assert model.validate_name("") is False
        assert model.validate_name("   ") is False
        assert model.validate_name("А") is False


class TestClientCRUD:
    """Тесты CRUD операций клиента."""
    
    @pytest.fixture
    def db_driver(self):
        """Фикстура драйвера БД."""
        driver = DatabaseDriver()
        driver.connect()
        
        # Создаем таблицы
        with driver._get_cursor(dict_cursor=True) as cursor:
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
        
        yield driver
        
        # Очистка
        with driver._get_cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS clients CASCADE")
        driver.disconnect()
    
    @pytest.fixture
    def client_model(self, db_driver):
        """Фикстура модели клиента."""
        return ClientModel(db_driver)
    
    def test_create_client(self, client_model, sample_client_data):
        """Тест создания клиента."""
        client_id = client_model.create(**sample_client_data)
        
        assert client_id is not None
        assert isinstance(client_id, int)
        assert client_id > 0
    
    def test_create_client_invalid_email(self, client_model, sample_client_data):
        """Тест создания клиента с некорректным email."""
        sample_client_data["email"] = "invalid-email"
        
        with pytest.raises(ValueError, match="Некорректный формат email"):
            client_model.create(**sample_client_data)
    
    def test_create_client_invalid_phone(self, client_model, sample_client_data):
        """Тест создания клиента с некорректным телефоном."""
        sample_client_data["phone"] = "abc"
        
        with pytest.raises(ValueError, match="Некорректный формат телефона"):
            client_model.create(**sample_client_data)
    
    def test_create_client_invalid_name(self, client_model, sample_client_data):
        """Тест создания клиента с некорректным именем."""
        sample_client_data["name"] = "А"  # Слишком короткое
        
        with pytest.raises(ValueError, match="Имя должно содержать минимум"):
            client_model.create(**sample_client_data)
    
    def test_get_by_id(self, client_model, sample_client_data):
        """Тест получения клиента по ID."""
        client_id = client_model.create(**sample_client_data)
        client = client_model.get_by_id(client_id)
        
        assert client is not None
        assert client['name'] == sample_client_data['name']
        assert client['email'] == sample_client_data['email']
    
    def test_get_by_id_not_found(self, client_model):
        """Тест получения несуществующего клиента."""
        client = client_model.get_by_id(99999)
        assert client is None
    
    def test_get_by_email(self, client_model, sample_client_data):
        """Тест поиска клиента по email."""
        client_model.create(**sample_client_data)
        client = client_model.get_by_email(sample_client_data['email'])
        
        assert client is not None
        assert client['name'] == sample_client_data['name']
    
    def test_get_all(self, client_model, sample_client_data):
        """Тест получения всех клиентов."""
        client_model.create(**sample_client_data)
        clients = client_model.get_all()
        
        assert len(clients) > 0
    
    def test_update_client(self, client_model, sample_client_data):
        """Тест обновления клиента."""
        client_id = client_model.create(**sample_client_data)
        
        success = client_model.update(client_id, name="Новое Имя")
        assert success is True
        
        client = client_model.get_by_id(client_id)
        assert client['name'] == "Новое Имя"
    
    def test_delete_client(self, client_model, sample_client_data):
        """Тест удаления клиента."""
        client_id = client_model.create(**sample_client_data)
        
        success = client_model.delete(client_id)
        assert success is True
        
        client = client_model.get_by_id(client_id)
        assert client is None
    
    def test_search_clients(self, client_model, sample_client_data):
        """Тест поиска клиентов."""
        client_model.create(**sample_client_data)
        
        results = client_model.search("Тестовый")
        assert len(results) > 0
        
        results = client_model.search("NonExistent")
        assert len(results) == 0


class TestClientDuplicate:
    """Тесты обработки дубликатов."""
    
    @pytest.fixture
    def db_driver(self):
        """Фикстура драйвера БД."""
        driver = DatabaseDriver()
        driver.connect()
        
        with driver._get_cursor(dict_cursor=True) as cursor:
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
        
        yield driver
        
        with driver._get_cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS clients CASCADE")
        driver.disconnect()
    
    @pytest.fixture
    def client_model(self, db_driver):
        """Фикстура модели клиента."""
        return ClientModel(db_driver)
    
    def test_duplicate_email(self, client_model, sample_client_data):
        """Тест создания клиента с дублирующимся email."""
        client_model.create(**sample_client_data)
        
        # Попытка создать клиента с тем же email
        with pytest.raises(Exception):  # psycopg2.IntegrityError
            client_model.create(
                name="Другой Клиент",
                email=sample_client_data['email'],  # Дубликат
                phone="+79009876543"
            )
