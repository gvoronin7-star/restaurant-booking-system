# Система бронирования ресторана

Полнофункциональная система управления бронированиями столиков ресторана на базе PostgreSQL с CLI и GUI интерфейсами.

---

## Возможности

- ✅ Управление клиентами (CRUD с валидацией)
- ✅ Управление столиками (вместимость, локация, статус)
- ✅ Бронирования с проверкой доступности
- ✅ Защита от конфликтов (проверка пересечений)
- ✅ Быстрое бронирование (клиент + бронь за один вызов)
- ✅ Расписание на день с детализацией
- ✅ Матрица доступности столиков
- ✅ Статистика и отчёты
- ✅ Логирование операций
- ✅ CLI интерфейс для администраторов
- ✅ GUI интерфейс (tkinter)
- ✅ Система тестирования (pytest)

## Быстрый старт

### Установка

```bash
# Клонирование
git clone https://github.com/YOUR_USERNAME/restaurant-booking-system.git
cd restaurant-booking-system

# Установка зависимостей
pip install -r requirements.txt

# Настройка .env
cp .env.example .env
# Отредактируйте .env с вашими данными
```

### Запуск

```bash
# Демонстрация
python main.py

# CLI интерфейс
python cli.py

# GUI интерфейс
python gui.py
```

## Документация

- [USER_GUIDE.md](USER_GUIDE.md) - Полное руководство пользователя
- [CONTRIBUTING.md](CONTRIBUTING.md) - Руководство для контрибьюторов

## Тестирование

```bash
# Быстрые тесты (без БД)
python tests/quick_tests.py

# Все тесты
python -m pytest -v
```

## Структура проекта

```
├── postgres_driver.py    # Драйвер БД
├── backend.py           # Бизнес-логика
├── cli.py               # CLI интерфейс
├── gui.py               # GUI интерфейс
├── main.py              # Демонстрация
├── run_tests.py         # Запуск тестов
├── pytest.ini           # Конфигурация pytest
├── requirements.txt     # Зависимости
├── .env.example         # Пример конфигурации
├── README.md            # Этот файл
├── USER_GUIDE.md        # Руководство пользователя
├── CONTRIBUTING.md      # Для контрибьюторов
├── LICENSE              # Лицензия
├── prepare_github.sh    # Скрипт подготовки к GitHub
│
├── models/              # Модели данных
│   ├── client.py
│   ├── table.py
│   └── booking.py
│
└── tests/               # Тесты
    ├── conftest.py
    ├── quick_tests.py
    ├── test_client.py
    ├── test_table.py
    ├── test_booking.py
    └── test_integration.py
```

## Требования

- Python 3.8+
- PostgreSQL 12+
- psycopg2-binary
- python-dotenv
- tkinter (встроен в Python)

## Лицензия

MIT License - см. [LICENSE](LICENSE)
