"""
Тестовый файл для подключения к PostgreSQL.
Требует библиотеки: pip install psycopg2-binary python-dotenv
"""

import os
import sys

# Настройка кодировки для Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from contextlib import contextmanager


# Цвета для терминала
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    PURPLE = '\033[95m'


def print_header(text: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text.center(50)}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 50}{Colors.RESET}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}[+] {text}{Colors.RESET}")


def print_error(text: str):
    print(f"{Colors.RED}[-] {text}{Colors.RESET}")


def print_info(text: str):
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")

# Загрузка переменных из .env файла
load_dotenv()

# Параметры подключения из переменных окружения
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "testdb"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "")
}


@contextmanager
def get_connection(config=None):
    """Контекстный менеджер для работы с подключением."""
    cfg = config or DB_CONFIG
    conn = psycopg2.connect(**cfg)
    try:
        yield conn
    finally:
        conn.close()


def test_connection(config=None):
    """Проверка подключения к БД."""
    cfg = config or DB_CONFIG
    try:
        with get_connection(cfg) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                print_success("Подключение к PostgreSQL успешно!")
                print(f"  {Colors.YELLOW}Хост:{Colors.RESET} {cfg['host']}:{cfg['port']}")
                print(f"  {Colors.YELLOW}База данных:{Colors.RESET} {cfg['database']}")
                print(f"  {Colors.YELLOW}Пользователь:{Colors.RESET} {cfg['user']}")
                print(f"\n  {Colors.PURPLE}Версия PostgreSQL:{Colors.RESET}")
                print(f"  {version[0]}\n")
                return True
    except psycopg2.OperationalError as e:
        print_error(f"Ошибка подключения: {e}")
        return False
    except Exception as e:
        print_error(f"Ошибка: {e}")
        return False


def execute_query(query, params=None, config=None):
    """Выполнение SQL-запроса."""
    with get_connection(config) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            if query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            conn.commit()
            return cursor.rowcount


if __name__ == "__main__":
    print_header("Тестирование подключения к PostgreSQL")
    test_connection()
