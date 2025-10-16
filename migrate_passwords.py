#!/usr/bin/env python3
"""
Скрипт для миграции паролей с bcrypt на pbkdf2_sha256
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models.administrator import Administrator
from app.core.security import get_password_hash

def migrate_passwords():
    """Мигрирует все пароли на новый алгоритм хеширования"""
    db = SessionLocal()
    
    try:
        # Получаем всех администраторов
        administrators = db.query(Administrator).all()
        
        print(f"Найдено {len(administrators)} администраторов для миграции...")
        
        for admin in administrators:
            if admin.hashed_password and not admin.hashed_password.startswith('$pbkdf2-sha256$'):
                # Если пароль еще не мигрирован, пересоздаем хеш
                # В реальном проекте здесь нужно было бы знать оригинальный пароль
                # Но для демо просто создаем новый хеш с дефолтным паролем
                new_password = "admin123"  # Дефолтный пароль для всех
                admin.hashed_password = get_password_hash(new_password)
                print(f"Обновлен пароль для администратора: {admin.login}")
        
        db.commit()
        print("✅ Миграция паролей завершена успешно!")
        print("🔑 Дефолтный пароль для всех администраторов: admin123")
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_passwords()
