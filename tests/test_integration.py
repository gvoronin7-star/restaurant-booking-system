"""
Интеграционные тесты для системы бронирования ресторана.
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from postgres_driver import DatabaseDriver
from backend import RestaurantBackend


class TestFullBookingFlow:
    """Тест полного цикла бронирования."""
    
    @pytest.fixture
    def backend(self):
        """Фикстура backend."""
        be = RestaurantBackend()
        be.connect()
        be.initialize_database()
        
        yield be
        
        be.disconnect()
    
    def test_full_booking_flow(self, backend, test_date):
        """
        Полный цикл: создание клиента → бронирование → подтверждение → завершение.
        """
        # 1. Создаем клиента
        client_id = backend.clients.create(
            name="Интеграционный Клиент",
            email=f"integration_{datetime.now().timestamp()}@test.com",
            phone="+79001234567"
        )
        assert client_id is not None
        
        # 2. Находим доступный столик
        table = backend.find_table_for_group(4, test_date, "14:00", "16:00")
        assert table is not None
        
        # 3. Создаем бронирование
        booking_id = backend.bookings.create(
            client_id=client_id,
            table_id=table['id'],
            date=test_date,
            start_time="14:00",
            end_time="16:00",
            guest_count=3,
            status="pending"
        )
        assert booking_id is not None
        
        # 4. Подтверждаем бронирование
        success = backend.bookings.confirm(booking_id)
        assert success is True
        
        # 5. Проверяем, что столик теперь недоступен
        available = backend.tables.get_available(test_date, "15:00")
        table_ids = [t['id'] for t in available]
        assert table['id'] not in table_ids
        
        # 6. Завершаем бронирование
        success = backend.bookings.complete(booking_id)
        assert success is True
        
        # 7. Проверяем историю клиента
        client_bookings = backend.bookings.get_by_client(client_id)
        assert len(client_bookings) > 0
    
    def test_quick_booking(self, backend, test_date):
        """Тест быстрого бронирования."""
        result = backend.quick_book(
            client_name="Быстрый Клиент",
            client_email=f"quick_{datetime.now().timestamp()}@test.com",
            client_phone="+79001234567",
            guest_count=2,
            date=test_date,
            start_time="18:00",
            duration_hours=2
        )
        
        assert result['booking_id'] is not None
        assert result['table'] is not None
        assert result['client'] is not None
    
    def test_booking_conflict_prevention(self, backend, test_date):
        """Тест предотвращения конфликтов."""
        # Создаем клиента и столик
        client_id = backend.clients.create(
            name="Конфликт Тест",
            email=f"conflict_{datetime.now().timestamp()}@test.com",
            phone="+79001234567"
        )
        
        table = backend.find_table_for_group(4, test_date, "12:00", "14:00")
        
        # Создаем первое бронирование
        booking_id = backend.bookings.create(
            client_id=client_id,
            table_id=table['id'],
            date=test_date,
            start_time="12:00",
            end_time="14:00",
            guest_count=3,
            status="confirmed"
        )
        
        # Пытаемся создать пересекающееся бронирование
        with pytest.raises(ValueError, match="занят"):
            backend.bookings.create(
                client_id=client_id,
                table_id=table['id'],
                date=test_date,
                start_time="13:00",  # Пересекается
                end_time="15:00",
                guest_count=3
            )
    
    def test_cascade_delete(self, backend, test_date):
        """Тест каскадного удаления."""
        # Создаем клиента с бронированием
        client_id = backend.clients.create(
            name="Каскад Тест",
            email=f"cascade_{datetime.now().timestamp()}@test.com",
            phone="+79001234567"
        )
        
        table = backend.find_table_for_group(4, test_date, "10:00", "12:00")
        
        booking_id = backend.bookings.create(
            client_id=client_id,
            table_id=table['id'],
            date=test_date,
            start_time="10:00",
            end_time="12:00",
            guest_count=2
        )
        
        # Удаляем клиента
        backend.clients.delete(client_id)
        
        # Проверяем, что бронирование удалено
        booking = backend.bookings.get_by_id(booking_id)
        assert booking is None
    
    def test_table_capacity_validation(self, backend, test_date):
        """Тест проверки вместимости столика."""
        client_id = backend.clients.create(
            name="Вместимость Тест",
            email=f"capacity_{datetime.now().timestamp()}@test.com",
            phone="+79001234567"
        )
        
        # Находим маленький столик
        table = backend.tables.get_by_capacity(2, 2)[0]
        
        # Пытаемся забронировать больше гостей чем вместимость
        with pytest.raises(ValueError, match="вместит только"):
            backend.bookings.create(
                client_id=client_id,
                table_id=table['id'],
                date=test_date,
                start_time="10:00",
                end_time="12:00",
                guest_count=10  # Больше чем вместимость
            )
    
    def test_daily_schedule(self, backend, test_date):
        """Тест расписания на день."""
        # Создаем несколько бронирований
        client_id = backend.clients.create(
            name="Расписание Тест",
            email=f"schedule_{datetime.now().timestamp()}@test.com",
            phone="+79001234567"
        )
        
        table = backend.find_table_for_group(4, test_date, "11:00", "13:00")
        
        backend.bookings.create(
            client_id=client_id,
            table_id=table['id'],
            date=test_date,
            start_time="11:00",
            end_time="13:00",
            guest_count=3,
            status="confirmed"
        )
        
        # Получаем расписание
        schedule = backend.get_daily_schedule(test_date)
        assert len(schedule) > 0
    
    def test_statistics(self, backend, test_date):
        """Тест статистики."""
        # Создаем бронирование
        client_id = backend.clients.create(
            name="Статистика Тест",
            email=f"stats_{datetime.now().timestamp()}@test.com",
            phone="+79001234567"
        )
        
        table = backend.find_table_for_group(4, test_date, "16:00", "18:00")
        
        backend.bookings.create(
            client_id=client_id,
            table_id=table['id'],
            date=test_date,
            start_time="16:00",
            end_time="18:00",
            guest_count=4,
            status="confirmed"
        )
        
        # Проверяем статистику
        today = datetime.now().strftime("%Y-%m-%d")
        summary = backend.bookings.get_daily_summary(today)
        
        assert summary['total_bookings'] >= 1
        assert summary['confirmed'] >= 1


class TestEdgeCases:
    """Тесты граничных случаев."""
    
    @pytest.fixture
    def backend(self):
        """Фикстура backend."""
        be = RestaurantBackend()
        be.connect()
        be.initialize_database()
        
        yield be
        
        be.disconnect()
    
    def test_empty_database(self, backend):
        """Тест работы с пустой базой."""
        clients = backend.clients.get_all()
        tables = backend.tables.get_all()
        bookings = backend.bookings.get_all()
        
        assert isinstance(clients, list)
        assert isinstance(tables, list)
        assert isinstance(bookings, list)
    
    def test_nonexistent_client(self, backend):
        """Тест работы с несуществующим клиентом."""
        client = backend.clients.get_by_id(99999)
        assert client is None
    
    def test_nonexistent_table(self, backend):
        """Тест работы с несуществующим столиком."""
        table = backend.tables.get_by_id(99999)
        assert table is None
    
    def test_nonexistent_booking(self, backend):
        """Тест работы с несуществующим бронированием."""
        booking = backend.bookings.get_by_id(99999)
        assert booking is None
    
    def test_booking_past_date(self, backend):
        """Тест создания бронирования на прошедшую дату."""
        client_id = backend.clients.create(
            name="Прошлое Тест",
            email=f"past_{datetime.now().timestamp()}@test.com",
            phone="+79001234567"
        )
        
        table = backend.tables.get_all()[0]
        
        past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        with pytest.raises(ValueError, match="Некорректная дата"):
            backend.bookings.create(
                client_id=client_id,
                table_id=table['id'],
                date=past_date,
                start_time="12:00",
                end_time="14:00",
                guest_count=2
            )
    
    def test_update_nonexistent_booking(self, backend):
        """Тест обновления несуществующего бронирования."""
        success = backend.bookings.update(
            booking_id=99999,
            guest_count=5
        )
        assert success is False
    
    def test_cancel_nonexistent_booking(self, backend):
        """Тест отмены несуществующего бронирования."""
        success = backend.cancel_booking_with_notification(99999)
        assert success is False
