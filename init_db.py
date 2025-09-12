#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.init_db import init_database

if __name__ == "__main__":
    print("🚀 Инициализация базы данных...")
    try:
        init_database()
        print("✅ База данных успешно инициализирована!")
    except Exception as e:
        print(f"❌ Ошибка при инициализации базы данных: {e}")
        sys.exit(1)
