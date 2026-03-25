"""
Пример использования DatabaseDriver.
"""

from database import DatabaseDriver


def main():
    # Подключение через контекстный менеджер (автоматически закрывает соединение)
    with DatabaseDriver() as db:
        # Очистка таблицы перед тестом
        db.query("DELETE FROM users")
        print("Table cleared\n")
        
        # Проверка версии PostgreSQL
        print(f"Версия PostgreSQL: {db.get_version()}\n")
        
        # Посмотрим какие таблицы есть в базе
        tables = db.query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        print(f"Таблицы в базе: {[t['table_name'] for t in tables]}\n")
        
        # Посмотрим структуру таблицы users
        columns = db.query("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users'
        """)
        print(f"Колонки таблицы users: {[(c['column_name'], c['data_type']) for c in columns]}\n")
        
        # ===== CREATE =====
        # Вставка одной записи (без автоинкремента - передаем id вручную)
        user_id = db.insert("users", {
            "id": 1,
            "name": "Ivan Ivanov",
            "age": 25
        })
        print(f"Created user with ID: 1")
        
        # Вставка нескольких записей
        db.insert_many("users", [
            {"id": 2, "name": "Petr Petrov", "age": 30},
            {"id": 3, "name": "Anna Sidorova", "age": 28},
        ])
        print("Created 2 users")
        
        # ===== READ =====
        # Получить одного пользователя
        user = db.select_one("users", {"id": user_id})
        print(f"\nUser: {user}")
        
        # Получить всех пользователей
        all_users = db.select_all("users", order_by="name")
        print(f"Total users: {len(all_users)}")
        
        # Проверка существования
        exists = db.exists("users", {"id": 1})
        print(f"User exists: {exists}")
        
        # Подсчет записей
        total = db.count("users")
        print(f"Total count: {total}")
        
        # ===== UPDATE =====
        updated = db.update("users", {"age": 26}, {"id": 1})
        print(f"\nUpdated rows: {updated}")
        
        # Проверка обновления
        user = db.select_one("users", {"id": 1})
        print(f"User age: {user['age']}")
        
        # ===== DELETE =====
        deleted = db.delete("users", {"id": 1})
        print(f"\nDeleted rows: {deleted}")
        
        # Удаление по ID
        db.delete_by_id("users", 2)
        print("Deleted user with ID=2")
        
        # Произвольный SQL-запрос
        result = db.query("SELECT COUNT(*) as cnt FROM users")
        print(f"Remaining users: {result[0]['cnt']}")


if __name__ == "__main__":
    main()
