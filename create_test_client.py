#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.client import Client

def create_test_client():
    db = SessionLocal()
    try:
        # Проверяем, существует ли тестовый клиент
        existing_client = db.query(Client).filter(Client.phone_number == "+996111111111").first()
        if existing_client:
            print("✅ Тестовый клиент уже существует:")
            print(f"   ID: {existing_client.id}")
            print(f"   Имя: {existing_client.first_name} {existing_client.last_name}")
            print(f"   Телефон: {existing_client.phone_number}")
            print(f"   Email: {existing_client.email}")
            print(f"   Статус: {'Активен' if existing_client.is_active else 'Заблокирован'}")
            return existing_client

        # Создаем тестового клиента
        test_client = Client(
            first_name="Тест",
            last_name="Клиент",
            phone_number="+996111111111",
            email="test@example.com",
            preferred_payment_method="cash",
            is_active=True
        )

        db.add(test_client)
        db.commit()
        db.refresh(test_client)

        print("✅ Тестовый клиент успешно создан:")
        print(f"   ID: {test_client.id}")
        print(f"   Имя: {test_client.first_name} {test_client.last_name}")
        print(f"   Телефон: {test_client.phone_number}")
        print(f"   Email: {test_client.email}")
        print(f"   Способ оплаты: {test_client.preferred_payment_method}")
        print(f"   Статус: {'Активен' if test_client.is_active else 'Заблокирован'}")
        print()
        print("🔑 Данные для входа:")
        print(f"   Номер телефона: +996 111 111 111")
        print(f"   SMS код: 1111")

        return test_client

    except Exception as e:
        print(f"❌ Ошибка при создании тестового клиента: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("👤 Создание тестового клиента...")
    print("=" * 50)
    create_test_client()
