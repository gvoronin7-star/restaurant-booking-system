"""
CLI интерфейс для системы бронирования ресторана.
"""

import sys
import os

# Настройка UTF-8 для Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from datetime import datetime, timedelta
from backend import RestaurantBackend


class CLIInterface:
    """Командный интерфейс для системы бронирования."""
    
    def __init__(self):
        self.backend = None
        self.running = True
    
    def print_header(self, text: str):
        print(f"\n{'=' * 50}")
        print(f"  {text}")
        print(f"{'=' * 50}\n")
    
    def print_menu(self):
        print("""
╔══════════════════════════════════════════════════╗
║       СИСТЕМА БРОНИРОВАНИЯ РЕСТОРАНА             ║
╠══════════════════════════════════════════════════╣
║  1. Создать/обновить таблицы БД                  ║
║  2. Загрузить демо-данные                        ║
║  3. Управление клиентами                         ║
║  4. Управление столиками                         ║
║  5. Управление бронированиями                    ║
║  6. Расписание на день                           ║
║  7. Быстрое бронирование                         ║
║  8. Поиск столика для группы                     ║
║  9. Статистика                                   ║
║  0. Выход                                        ║
╚══════════════════════════════════════════════════╝
        """)
    
    def connect(self):
        """Подключение к БД."""
        try:
            self.backend = RestaurantBackend()
            self.backend.connect()
            print("✓ Подключение к БД установлено")
            return True
        except Exception as e:
            print(f"✗ Ошибка подключения: {e}")
            return False
    
    def disconnect(self):
        """Отключение от БД."""
        if self.backend:
            self.backend.disconnect()
            print("✓ Подключение закрыто")
    
    def init_database(self):
        """Инициализация таблиц БД."""
        try:
            self.backend.initialize_database()
            print("✓ Таблицы созданы успешно")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def seed_data(self):
        """Загрузка демо-данных."""
        try:
            self.backend.seed_demo_data()
            print("✓ Демо-данные загружены")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def clients_menu(self):
        """Меню управления клиентами."""
        while True:
            print("""
╔══════════════════════════════════════════════════╗
║            УПРАВЛЕНИЕ КЛИЕНТАМИ                  ║
╠══════════════════════════════════════════════════╣
║  1. Список клиентов                              ║
║  2. Добавить клиента                            ║
║  3. Найти по email                              ║
║  4. Поиск клиентов                              ║
║  5. Обновить данные                             ║
║  6. Удалить клиента                             ║
║  0. Назад                                        ║
╚══════════════════════════════════════════════════╝
            """)
            choice = input("Выберите действие: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._list_clients()
            elif choice == '2':
                self._add_client()
            elif choice == '3':
                self._find_client_by_email()
            elif choice == '4':
                self._search_clients()
            elif choice == '5':
                self._update_client()
            elif choice == '6':
                self._delete_client()
    
    def _list_clients(self):
        clients = self.backend.clients.get_all()
        if not clients:
            print("Клиентов не найдено")
            return
        print("\nСписок клиентов:")
        print("-" * 60)
        for c in clients:
            print(f"  ID: {c['id']} | {c['name']:20} | {c['email']:25} | {c['phone']}")
    
    def _add_client(self):
        try:
            name = input("Имя: ").strip()
            email = input("Email: ").strip()
            phone = input("Телефон: ").strip()
            
            client_id = self.backend.clients.create(name, email, phone)
            print(f"✓ Клиент создан с ID: {client_id}")
        except ValueError as e:
            print(f"✗ Ошибка валидации: {e}")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def _find_client_by_email(self):
        email = input("Email: ").strip()
        client = self.backend.clients.get_by_email(email)
        if client:
            print(f"\nНайден: {client['name']}, тел: {client['phone']}")
        else:
            print("Клиент не найден")
    
    def _search_clients(self):
        query = input("Поиск (имя, email или телефон): ").strip()
        results = self.backend.clients.search(query)
        if results:
            print(f"\nНайдено {len(results)} клиентов:")
            for c in results:
                print(f"  {c['id']}: {c['name']} - {c['email']}")
        else:
            print("Ничего не найдено")
    
    def _update_client(self):
        try:
            client_id = int(input("ID клиента: "))
            name = input("Новое имя (оставьте пустым): ").strip()
            email = input("Новый email (оставьте пустым): ").strip()
            phone = input("Новый телефон (оставьте пустым): ").strip()
            
            kwargs = {}
            if name: kwargs['name'] = name
            if email: kwargs['email'] = email
            if phone: kwargs['phone'] = phone
            
            if kwargs:
                success = self.backend.clients.update(client_id, **kwargs)
                print("✓ Обновлено" if success else "✗ Не обновлено")
            else:
                print("Нет данных для обновления")
        except ValueError as e:
            print(f"✗ Ошибка: {e}")
    
    def _delete_client(self):
        try:
            client_id = int(input("ID клиента: "))
            if self.backend.clients.delete(client_id):
                print("✓ Удалено")
            else:
                print("✗ Не найден")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def tables_menu(self):
        """Меню управления столиками."""
        while True:
            print("""
╔══════════════════════════════════════════════════╗
║            УПРАВЛЕНИЕ СТОЛИКАМИ                  ║
╠══════════════════════════════════════════════════╣
║  1. Список столиков                              ║
║  2. Добавить столик                             ║
║  3. Доступные столики на дату                   ║
║  4. Матрица доступности                         ║
║  5. Обновить статус                             ║
║  6. Удалить столик                              ║
║  0. Назад                                        ║
╚══════════════════════════════════════════════════╝
            """)
            choice = input("Выберите действие: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._list_tables()
            elif choice == '2':
                self._add_table()
            elif choice == '3':
                self._available_tables()
            elif choice == '4':
                self._availability_matrix()
            elif choice == '5':
                self._update_table_status()
            elif choice == '6':
                self._delete_table()
    
    def _list_tables(self):
        tables = self.backend.tables.get_all()
        if not tables:
            print("Столиков не найдено")
            return
        print("\nСписок столиков:")
        print("-" * 70)
        for t in tables:
            print(f"  {t['table_number']:5} | вместимость: {t['capacity']:2} | "
                  f"локация: {t['location']:12} | статус: {t['status']}")
    
    def _add_table(self):
        try:
            number = input("Номер столика: ").strip()
            capacity = int(input("Вместимость (1-20): "))
            location = input("Локация (main_hall/terrace/vip_room/bar): ").strip()
            
            table_id = self.backend.tables.create(number, capacity, location)
            print(f"✓ Столик создан с ID: {table_id}")
        except ValueError as e:
            print(f"✗ Ошибка: {e}")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def _available_tables(self):
        date = input("Дата (YYYY-MM-DD, пусто = сегодня): ").strip()
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        time = input("Время (HH:MM, пусто = сейчас): ").strip()
        if not time:
            time = datetime.now().strftime("%H:%M")
        
        tables = self.backend.tables.get_available(date, time)
        print(f"\nДоступные столики на {date} в {time}:")
        for t in tables:
            print(f"  {t['table_number']} - вместимость: {t['capacity']}, {t['location']}")
    
    def _availability_matrix(self):
        date = input("Дата (YYYY-MM-DD, пусто = сегодня): ").strip()
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        matrix = self.backend.tables.get_availability_matrix(date)
        print(f"\nМатрица доступности на {date}:")
        print("-" * 60)
        
        time_slots = [f"{h:02d}:00" for h in range(10, 23)]
        
        # Заголовок
        header = "Стол/Время".ljust(10)
        for slot in time_slots:
            header += f" {slot[0:2]}"
        print(header)
        print("-" * 60)
        
        for table_num, data in matrix.items():
            row = table_num.ljust(10)
            for slot in time_slots:
                status = "✓" if data['slots'].get(slot, False) else "✗"
                row += f" {status}"
            print(row)
    
    def _update_table_status(self):
        try:
            table_id = int(input("ID столика: "))
            status = input("Статус (available/occupied/reserved/maintenance): ").strip()
            
            if self.backend.tables.update_status(table_id, status):
                print("✓ Статус обновлён")
            else:
                print("✗ Не обновлено")
        except ValueError as e:
            print(f"✗ Ошибка: {e}")
    
    def _delete_table(self):
        try:
            table_id = int(input("ID столика: "))
            if self.backend.tables.delete(table_id):
                print("✓ Удалён")
            else:
                print("✗ Не найден")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def bookings_menu(self):
        """Меню управления бронированиями."""
        while True:
            print("""
╔══════════════════════════════════════════════════╗
║         УПРАВЛЕНИЕ БРОНИРОВАНИЯМИ                ║
╠══════════════════════════════════════════════════╣
║  1. Список бронирований                          ║
║  2. Создать бронирование                         ║
║  3. Бронирования на дату                        ║
║  4. Предстоящие бронирования                    ║
║  5. Бронирования клиента                        ║
║  6. Подтвердить бронирование                    ║
║  7. Отменить бронирование                       ║
║  8. Завершить бронирование                      ║
║  9. Обновить бронирование                       ║
║  0. Назад                                        ║
╚══════════════════════════════════════════════════╝
            """)
            choice = input("Выберите действие: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._list_bookings()
            elif choice == '2':
                self._create_booking()
            elif choice == '3':
                self._bookings_by_date()
            elif choice == '4':
                self._upcoming_bookings()
            elif choice == '5':
                self._client_bookings()
            elif choice == '6':
                self._confirm_booking()
            elif choice == '7':
                self._cancel_booking()
            elif choice == '8':
                self._complete_booking()
            elif choice == '9':
                self._update_booking()
    
    def _list_bookings(self):
        status = input("Фильтр по статусу (пусто = все): ").strip()
        bookings = self.backend.bookings.get_all(status or None)
        
        if not bookings:
            print("Бронирований не найдено")
            return
        
        print("\nСписок бронирований:")
        print("-" * 80)
        for b in bookings:
            date = b['booking_date']
            start = str(b['start_time'])[:5]
            end = str(b['end_time'])[:5]
            print(f"  #{b['id']} | {date} {start}-{end} | стол {b['table_number']:4} | "
                  f"клиент: {b['client_name']:15} | {b['guest_count']} гостей | {b['status']}")
    
    def _create_booking(self):
        try:
            client_id = int(input("ID клиента: "))
            table_id = int(input("ID столика: "))
            date = input("Дата (YYYY-MM-DD): ").strip()
            start = input("Время начала (HH:MM): ").strip()
            end = input("Время окончания (HH:MM): ").strip()
            guests = int(input("Количество гостей: "))
            notes = input("Заметки (пусто): ").strip()
            
            booking_id = self.backend.bookings.create(
                client_id, table_id, date, start, end, guests, notes
            )
            print(f"✓ Бронирование создано с ID: {booking_id}")
        except ValueError as e:
            print(f"✗ Ошибка: {e}")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def _bookings_by_date(self):
        date = input("Дата (YYYY-MM-DD, пусто = сегодня): ").strip()
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        bookings = self.backend.bookings.get_by_date(date)
        
        if not bookings:
            print(f"Нет бронирований на {date}")
            return
        
        print(f"\nБронирования на {date}:")
        print("-" * 70)
        for b in bookings:
            start = str(b['start_time'])[:5]
            end = str(b['end_time'])[:5]
            print(f"  {start}-{end} | стол {b['table_number']} | "
                  f"{b['client_name']} ({b['guest_count']} гостей) | {b['status']}")
    
    def _upcoming_bookings(self):
        limit = int(input("Количество (по умолчанию 10): ") or "10")
        bookings = self.backend.bookings.get_upcoming(limit)
        
        if not bookings:
            print("Нет предстоящих бронирований")
            return
        
        print("\nПредстоящие бронирования:")
        print("-" * 70)
        for b in bookings:
            date = b['booking_date']
            start = str(b['start_time'])[:5]
            end = str(b['end_time'])[:5]
            print(f"  {date} {start}-{end} | стол {b['table_number']} | "
                  f"{b['client_name']} | {b['guest_count']} гостей")
    
    def _client_bookings(self):
        try:
            client_id = int(input("ID клиента: "))
            bookings = self.backend.bookings.get_by_client(client_id)
            
            if not bookings:
                print("Нет бронирований")
                return
            
            print("\nБронирования клиента:")
            for b in bookings:
                date = b['booking_date']
                start = str(b['start_time'])[:5]
                end = str(b['end_time'])[:5]
                print(f"  {date} {start}-{end} | стол {b['table_number']} | {b['status']}")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def _confirm_booking(self):
        try:
            booking_id = int(input("ID бронирования: "))
            if self.backend.bookings.confirm(booking_id):
                print("✓ Подтверждено")
            else:
                print("✗ Не найдено")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def _cancel_booking(self):
        try:
            booking_id = int(input("ID бронирования: "))
            if self.backend.cancel_booking_with_notification(booking_id):
                print("✓ Отменено")
            else:
                print("✗ Не найдено")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def _complete_booking(self):
        try:
            booking_id = int(input("ID бронирования: "))
            if self.backend.bookings.complete(booking_id):
                print("✓ Завершено")
            else:
                print("✗ Не найдено")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def _update_booking(self):
        try:
            booking_id = int(input("ID бронирования: "))
            print("Оставьте поле пустым, чтобы не изменять:")
            
            table_id = input("Новый ID столика: ").strip()
            date = input("Новая дата (YYYY-MM-DD): ").strip()
            start = input("Новое время начала (HH:MM): ").strip()
            end = input("Новое время окончания (HH:MM): ").strip()
            guests = input("Новое количество гостей: ").strip()
            
            kwargs = {}
            if table_id: kwargs['table_id'] = int(table_id)
            if date: kwargs['date'] = date
            if start: kwargs['start_time'] = start
            if end: kwargs['end_time'] = end
            if guests: kwargs['guest_count'] = int(guests)
            
            if kwargs:
                if self.backend.bookings.update(booking_id, **kwargs):
                    print("✓ Обновлено")
                else:
                    print("✗ Не обновлено")
            else:
                print("Нет данных для обновления")
        except ValueError as e:
            print(f"✗ Ошибка: {e}")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def daily_schedule(self):
        """Расписание на день."""
        date = input("Дата (YYYY-MM-DD, пусто = сегодня): ").strip()
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        schedule = self.backend.get_daily_schedule(date)
        
        if not schedule:
            print(f"Нет бронирований на {date}")
            return
        
        print(f"\n=== РАСПИСАНИЕ НА {date} ===\n")
        for s in schedule:
            start = str(s['start_time'])[:5]
            end = str(s['end_time'])[:5]
            print(f"  {start} - {end}")
            print(f"    Столик: {s['table_number']} ({s['location']})")
            print(f"    Клиент: {s['client_name']}, тел: {s['client_phone']}")
            print(f"    Гостей: {s['guest_count']}, статус: {s['status']}")
            if s.get('notes'):
                print(f"    Заметки: {s['notes']}")
            print()
    
    def quick_booking(self):
        """Быстрое бронирование."""
        try:
            print("\n=== БЫСТРОЕ БРОНИРОВАНИЕ ===\n")
            
            name = input("Имя клиента: ").strip()
            email = input("Email: ").strip()
            phone = input("Телефон: ").strip()
            guests = int(input("Количество гостей: "))
            date = input("Дата (YYYY-MM-DD): ").strip()
            start = input("Время начала (HH:MM): ").strip()
            
            result = self.backend.quick_book(
                name, email, phone, guests, date, start
            )
            
            print("\n✓ Бронирование создано!")
            print(f"  ID: {result['booking_id']}")
            print(f"  Клиент: {result['client']['name']}")
            print(f"  Столик: {result['table']['table_number']} "
                  f"(вместимость: {result['table']['capacity']})")
            print(f"  Время: {result['time']}")
            print(f"  Гостей: {result['guests']}")
            
        except ValueError as e:
            print(f"✗ Ошибка: {e}")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def find_table_for_group(self):
        """Поиск столика для группы."""
        try:
            guests = int(input("Количество гостей: "))
            date = input("Дата (YYYY-MM-DD): ").strip()
            start = input("Время начала (HH:MM): ").strip()
            end = input("Время окончания (HH:MM): ").strip()
            
            table = self.backend.find_table_for_group(guests, date, start, end)
            
            if table:
                print(f"\n✓ Найден столик: {table['table_number']}")
                print(f"  Вместимость: {table['capacity']}")
                print(f"  Локация: {table['location']}")
            else:
                print("\n✗ Нет доступных столиков")
                
        except ValueError as e:
            print(f"✗ Ошибка: {e}")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def statistics(self):
        """Статистика."""
        print("\n=== СТАТИСТИКА ===\n")
        
        # Сводка за сегодня
        today = datetime.now().strftime("%Y-%m-%d")
        summary = self.backend.bookings.get_daily_summary(today)
        
        print(f"СЕГОДНЯ ({today}):")
        print(f"  Всего бронирований: {summary['total_bookings']}")
        print(f"  Подтверждено: {summary['confirmed']}")
        print(f"  Ожидают: {summary['pending']}")
        print(f"  Отменено: {summary['cancelled']}")
        print(f"  Всего гостей: {summary['total_guests'] or 0}")
        
        # Статистика за неделю
        start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        end = datetime.now().strftime("%Y-%m-%d")
        stats = self.backend.bookings.get_statistics(start, end)
        
        print(f"\nЗА НЕДЕЛЮ ({start} - {end}):")
        print(f"  Всего бронирований: {stats['total_bookings']}")
        print(f"  Завершено: {stats['completed']}")
        print(f"  Отменено: {stats['cancelled']}")
        print(f"  Неявки: {stats['no_shows']}")
        print(f"  Среднее число гостей: {stats['avg_guests']:.1f}")
    
    def run(self):
        """Запуск CLI."""
        if not self.connect():
            return
        
        while self.running:
            self.print_menu()
            choice = input("Выберите действие: ").strip()
            
            if choice == '0':
                self.running = False
            elif choice == '1':
                self.init_database()
            elif choice == '2':
                self.seed_data()
            elif choice == '3':
                self.clients_menu()
            elif choice == '4':
                self.tables_menu()
            elif choice == '5':
                self.bookings_menu()
            elif choice == '6':
                self.daily_schedule()
            elif choice == '7':
                self.quick_booking()
            elif choice == '8':
                self.find_table_for_group()
            elif choice == '9':
                self.statistics()
        
        self.disconnect()
        print("\nДо свидания!")


def main():
    """Точка входа."""
    cli = CLIInterface()
    cli.run()


if __name__ == "__main__":
    main()
