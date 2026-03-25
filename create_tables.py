"""
Скрипт для создания тестовой таблицы users.
"""

from database import DatabaseDriver


def create_tables():
    """Создание таблицы users."""
    with DatabaseDriver() as db:
        # Удаление таблицы если существует
        db.query("DROP TABLE IF EXISTS users CASCADE")
        
        # Создание таблицы
        db.query("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Таблица users создана!")


if __name__ == "__main__":
    create_tables()
