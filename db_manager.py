import sqlite3
import os
from datetime import datetime

DB_PATH = "warehouse.db"

def get_connection():
    """Возвращает подключение к базе данных"""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Создает таблицы базы данных, если они не существуют, и заполняет их тестовыми данными"""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Таблица товаров (складские запасы)
    cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT UNIQUE, name TEXT, qty INTEGER, lot_number TEXT, quality_status TEXT, location TEXT)")

    # 2. Таблица задач ТСД (терминалов сбора данных)
    cursor.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT, status TEXT, target_sku TEXT, target_qty INTEGER, worker_name TEXT)")

    # 3. Таблица складских документов и логов
    cursor.execute("CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY AUTOINCREMENT, doc_type TEXT, timestamp TEXT, content TEXT)")

    conn.commit()

    # Заполнение тестовыми данными, если таблица товаров пуста
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        test_products = [
            ("11111", "Электронные процессоры Intel i9", 150, "LOT-2026-A", "APPROVED", "A1-02"),
            ("22222", "Кабель оптический судовой 100м", 40, "LOT-2026-B", "APPROVED", "B3-12"),
            ("33333", "Датчики температуры промышленные", 200, "LOT-2026-C", "PENDING", "A2-05"),
            ("44444", "Контроллеры управления Siemens", 15, "LOT-2026-D", "BLOCKED", "C1-01"),
            ("55555", "Блоки питания MeanWell 24V", 85, "LOT-2026-E", "APPROVED", "B1-04")
        ]
        cursor.executemany("INSERT INTO products (sku, name, qty, lot_number, quality_status, location) VALUES (?, ?, ?, ?, ?, ?)", test_products)
        
        # Добавим тестовую задачу для ТСД
        cursor.execute("INSERT INTO tasks (description, status, target_sku, target_qty, worker_name) VALUES (?, ?, ?, ?, ?)", ('Собрать партию контроллеров для отгрузки', 'PENDING', '55555', 10, 'Кладовщик Иван'))
        
        # Добавим запись об инициализации системы в лог
        cursor.execute("INSERT INTO documents (doc_type, timestamp, content) VALUES (?, ?, ?)", ('SYSTEM', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Инициализация базы данных WMS. Созданы стартовые складские остатки.'))

        conn.commit()

    conn.close()

# Инициализируем БД при импорте модуля
if not os.path.exists(DB_PATH):
    init_db()
else:
    init_db()
