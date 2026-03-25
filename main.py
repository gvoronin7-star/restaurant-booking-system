"""
Main.py - пример использования системы бронирования ресторана.
Демонстрирует: клиенты, столики, бронирования, проверку доступности.
"""

import sys

# Настройка UTF-8 для Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from datetime import datetime, timedelta
from backend import RestaurantBackend


def print_header(text: str):
    print(f"\n{'=' * 50}")
    print(f"  {text}")
    print(f"{'=' * 50}\n")


def main():
    """Демонстрация системы бронирования ресторана."""
    
    # Используем контекстный менеджер для автоматического подключения/отключения
    with RestaurantBackend() as backend:
        
        # 1. Создание таблиц БД
        print_header("Создание таблиц БД")
        backend.initialize_database()
        
        # 2. Загрузка демо-данных
        print_header("Загрузка демо-данных")
        backend.seed_demo_data()
        
        # 3. Работа с клиентами
        print_header("Управление клиентами")
        
        # Добавим нового клиента
        client_id = backend.clients.create(
            "Николай Иванов",
            "nikolay@example.com",
            "+79001234567"
        )
        print(f"Создан клиент: Николай Иванов (ID: {client_id})")
        
        # Поиск клиента по email
        client = backend.clients.get_by_email("ivan@example.com")
        if client:
            print(f"Найден клиент: {client['name']}, телефон: {client['phone']}")
        
        # 4. Работа со столиками
        print_header("Управление столиками")
        
        # Добавим новый столик
        table_id = backend.tables.create("VIP-1", 10, "vip_room")
        print(f"Создан столик VIP-1 (ID: {table_id})")
        
        # Получим все столики
        tables = backend.tables.get_all()
        print("\nВсе столики:")
        for t in tables:
            print(f"  {t['table_number']}: вместимость {t['capacity']}, "
                  f"локация: {t['location']}, статус: {t['status']}")
        
        # 5. Проверка доступности столиков
        print_header("Проверка доступности")
        today = datetime.now().strftime("%Y-%m-%d")
        available = backend.tables.get_available(today, "18:00")
        print(f"Доступные столики на {today} в 18:00:")
        for t in available:
            print(f"  {t['table_number']} (вместимость: {t['capacity']})")
        
        # 6. Создание бронирования
        print_header("Создание бронирования")
        
        # Найдём подходящий столик
        table = backend.find_table_for_group(4, today, "19:00", "21:00")
        if table:
            print(f"Найден столик: {table['table_number']}")
            
            # Создаём бронь
            booking_id = backend.bookings.create(
                client_id=client_id,
                table_id=table['id'],
                date=today,
                start_time="19:00",
                end_time="21:00",
                guest_count=4,
                status="confirmed"
            )
            print(f"Создано бронирование (ID: {booking_id})")
        else:
            print("Нет доступных столиков")
        
        # 7. Проверка конфликтов
        print_header("Проверка конфликтов")
        
        # Попробуем создать бронь на то же время
        if table:
            try:
                # Попытка создать бронь на занятое время
                backend.bookings.create(
                    client_id=client_id,
                    table_id=table['id'],
                    date=today,
                    start_time="19:30",  # Пересекается с существующей
                    end_time="21:30",
                    guest_count=3
                )
            except ValueError as e:
                print(f"Конфликт обнаружен: {e}")
        
        # 8. Расписание на день
        print_header("Расписание на день")
        schedule = backend.get_daily_schedule(today)
        print(f"Бронирования на {today}:")
        for b in schedule:
            start = str(b['start_time'])[:5]
            end = str(b['end_time'])[:5]
            print(f"  {start}-{end} | Стол {b['table_number']} | "
                  f"{b['client_name']} ({b['guest_count']} гостей) | {b['status']}")
        
        # 9. Быстрое бронирование
        print_header("Быстрое бронирование")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        try:
            result = backend.quick_book(
                client_name="Анна Смирнова",
                client_email="anna@example.com",
                client_phone="+79009876543",
                guest_count=2,
                date=tomorrow,
                start_time="20:00",
                duration_hours=2
            )
            print(f"Быстрое бронирование создано:")
            print(f"  ID: {result['booking_id']}")
            print(f"  Клиент: {result['client']['name']}")
            print(f"  Столик: {result['table']['table_number']}")
            print(f"  Время: {result['time']}")
        except Exception as e:
            print(f"Ошибка: {e}")
        
        # 10. Статистика
        print_header("Статистика")
        summary = backend.bookings.get_daily_summary(today)
        print(f"Сводка за {today}:")
        print(f"  Всего бронирований: {summary['total_bookings']}")
        print(f"  Подтверждено: {summary['confirmed']}")
        print(f"  Ожидают: {summary['pending']}")
        print(f"  Отменено: {summary['cancelled']}")
        print(f"  Всего гостей: {summary['total_guests'] or 0}")
        
        # 11. Отмена бронирования
        print_header("Отмена бронирования")
        if schedule:
            booking_to_cancel = schedule[0]['id']
            success = backend.cancel_booking_with_notification(booking_to_cancel)
            print(f"Бронирование #{booking_to_cancel} отменено: {success}")
        
        # 12. Матрица доступности
        print_header("Матрица доступности столиков")
        matrix = backend.tables.get_availability_matrix(today)
        
        print(f"\nДоступность на {today} (✓ - свободно, ✗ - занято):")
        print("-" * 50)
        
        time_slots = [f"{h:02d}:00" for h in range(10, 23)]
        header = "Стол/Время".ljust(10)
        for slot in time_slots:
            header += f" {slot[0:2]}"
        print(header)
        print("-" * 50)
        
        for table_num, data in matrix.items():
            row = table_num.ljust(10)
            for slot in time_slots:
                status = "✓" if data['slots'].get(slot, False) else "✗"
                row += f" {status}"
            print(row)
        
        print("\n[OK] Все операции выполнены успешно!")


if __name__ == "__main__":
    main()
