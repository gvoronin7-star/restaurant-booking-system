# Система бронирования ресторана

Полнофункциональная система управления бронированиями столиков ресторана на базе PostgreSQL.

## Возможности

- ✅ Управление клиентами (CRUD с валидацией)
- ✅ Управление столиками (вместимость, локация, статус)
- ✅ Бронирования с проверкой доступности
- ✅ Защита от конфликтов (проверка пересечений)
- ✅ Быстрое бронирование (создание клиента + бронь за один вызов)
- ✅ Расписание на день с детализацией
- ✅ Матрица доступности столиков
- ✅ Статистика и отчёты
- ✅ Логирование операций
- ✅ CLI интерфейс для администраторов
- ✅ GUI интерфейс (tkinter)
- ✅ Система тестирования

## Содержание

1. [Установка](#установка)
2. [Настройка](#настройка)
3. [Запуск](#запуск)
4. [Интерфейсы](#интерфейсы)
5. [Использование API](#использование-api)
6. [Тестирование](#тестирование)
7. [Структура проекта](#структура-проекта)

---

## Установка

### Требования

- Python 3.8+
- PostgreSQL 12+
- pip

### Шаги установки

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd restaurant-booking-system
```

2. **Создайте виртуальное окружение (рекомендуется):**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Настройте подключение к БД:**

Скопируйте файл `.env.example` в `.env` и заполните свои данные:
```bash
cp .env.example .env
```

Отредактируйте `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=restaurant_db
DB_USER=postgres
DB_PASSWORD=your_password
```

5. **Создайте базу данных:**
```sql
CREATE DATABASE restaurant_db;
```

---

## Настройка

### Структура базы данных

Система автоматически создаёт следующие таблицы:

#### Таблица `clients` (Клиенты)
| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL | Уникальный ID |
| name | TEXT | Имя клиента |
| email | TEXT | Email (уникальный) |
| phone | TEXT | Телефон |
| created_at | TIMESTAMP | Дата создания |

#### Таблица `tables` (Столики)
| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL | Уникальный ID |
| table_number | TEXT | Номер столика (уникальный) |
| capacity | INT | Вместимость (1-20) |
| location | TEXT | Локация |
| status | TEXT | Статус |

**Статусы столиков:**
- `available` - свободен
- `occupied` - занят
- `reserved` - зарезервирован
- `maintenance` - на обслуживании

#### Таблица `bookings` (Бронирования)
| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL | Уникальный ID |
| client_id | INT | ID клиента |
| table_id | INT | ID столика |
| booking_date | DATE | Дата бронирования |
| start_time | TIME | Время начала |
| end_time | TIME | Время окончания |
| guest_count | INT | Количество гостей |
| notes | TEXT | Заметки |
| status | TEXT | Статус бронирования |

**Статусы бронирований:**
- `pending` - ожидает подтверждения
- `confirmed` - подтверждено
- `cancelled` - отменено
- `completed` - завершено
- `no_show` - не явился

---

## Запуск

### Демонстрационный режим

Запустите `main.py` для демонстрации всех возможностей:
```bash
python main.py
```

### CLI интерфейс

Командный интерфейс для администраторов:
```bash
python cli.py
```

### GUI интерфейс

Графический интерфейс (tkinter):
```bash
python gui.py
```

---

## Интерфейсы

### CLI интерфейс

Меню CLI:
```
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
```

### GUI интерфейс

Вкладки GUI:
- **Расписание** - просмотр бронирований на дату
- **Доступность** - доступные столики, матрица
- **Бронирования** - управление бронированиями
- **Клиенты** - управление клиентами
- **Сталики** - управление столиками

---

## Использование API

### Подключение к БД

```python
from backend import RestaurantBackend

with RestaurantBackend() as backend:
    # Ваш код
```

### Работа с клиентами

```python
# Создание клиента
client_id = backend.clients.create(
    name="Иван Иванов",
    email="ivan@example.com",
    phone="+79001234567"
)

# Получение клиента
client = backend.clients.get_by_id(client_id)

# Поиск по email
client = backend.clients.get_by_email("ivan@example.com")

# Обновление
backend.clients.update(client_id, name="Новое имя")

# Удаление
backend.clients.delete(client_id)
```

### Работа со столиками

```python
# Создание столика
table_id = backend.tables.create(
    table_number="A1",
    capacity=4,
    location="main_hall"
)

# Доступные столики на время
available = backend.tables.get_available("2024-01-15", "19:00")

# Матрица доступности
matrix = backend.tables.get_availability_matrix("2024-01-15")
```

### Работа с бронированиями

```python
# Создание бронирования
booking_id = backend.bookings.create(
    client_id=1,
    table_id=1,
    date="2024-01-15",
    start_time="19:00",
    end_time="21:00",
    guest_count=4,
    status="confirmed"
)

# Проверка доступности
is_available = backend.bookings.check_availability(
    table_id=1,
    date="2024-01-15",
    start_time="19:00",
    end_time="21:00"
)

# Подтверждение/отмена/завершение
backend.bookings.confirm(booking_id)
backend.bookings.cancel(booking_id)
backend.bookings.complete(booking_id)
```

### Быстрое бронирование

Создаёт клиента и бронь за один вызов:

```python
result = backend.quick_book(
    client_name="Пётр Петров",
    client_email="petr@example.com",
    client_phone="+79001234567",
    guest_count=3,
    date="2024-01-20",
    start_time="18:00",
    duration_hours=2
)

print(result['booking_id'])  # ID бронирования
print(result['table']['table_number'])  # Номер столика
```

---

## Тестирование

### Быстрые тесты (без БД)

```bash
python tests/quick_tests.py
```

### Полные тесты

```bash
# Все тесты
python -m pytest -v

# Конкретный файл
python -m pytest tests/test_client.py -v

# Интеграционные тесты
python -m pytest tests/test_integration.py -v

# С покрытием кода
python -m pytest --cov=. --cov-report=html
```

---

## Структура проекта

```
restaurant-booking-system/
├── postgres_driver.py    # Драйвер БД
├── backend.py           # Бизнес-логика
├── cli.py               # CLI интерфейс
├── gui.py               # GUI интерфейс
├── main.py              # Демонстрация
├── run_tests.py         # Запуск тестов
├── pytest.ini           # Конфигурация pytest
├── requirements.txt     # Зависимости
├── .env.example         # Пример конфигурации
├── README.md            # Документация
├── USER_GUIDE.md        # Руководство пользователя
│
├── models/              # Модели данных
│   ├── __init__.py
│   ├── client.py
│   ├── table.py
│   └── booking.py
│
├── tests/               # Тесты
│   ├── __init__.py
│   ├── conftest.py
│   ├── quick_tests.py
│   ├── test_client.py
│   ├── test_table.py
│   ├── test_booking.py
│   └── test_integration.py
```

---

## Ограничения

- Время работы ресторана: 10:00 - 22:00
- Минимальная длительность бронирования: 1 час
- Максимальная длительность бронирования: 4 часа
- Максимальная вместимость столика: 20 гостей

---

## Устранение проблем

### Ошибка подключения к БД

Проверьте:
1. PostgreSQL запущен
2. Данные в `.env` корректны
3. База данных создана

### Ошибка "Нет доступных столиков"

Проверьте:
1. Созданы ли столики в базе
2. Свободны ли столики на указанное время

### Ошибка валидации

Система проверяет:
- Корректность email
- Корректность телефона
- Достаточную вместимость столика
- Отсутствие пересечений с другими бронированиями

---

## Лицензия

MIT License
