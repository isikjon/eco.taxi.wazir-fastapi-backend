#!/usr/bin/env python3
"""
Скрипт для добавления функции создания транзакций при пополнении баланса в диспетчерском API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import get_db
from app.models.driver import Driver
from app.models.transaction import DriverTransaction
from sqlalchemy.orm import Session
from datetime import datetime

def create_topup_transaction(driver_id: int, amount: float, description: str = "Пополнение баланса диспетчером"):
    """Создает транзакцию пополнения баланса"""
    db = next(get_db())
    
    try:
        # Создаем транзакцию пополнения
        topup_transaction = DriverTransaction(
            driver_id=driver_id,
            type="topup",
            amount=amount,
            description=description,
            status="completed",
            reference=f"TOPUP-{driver_id}-{int(datetime.now().timestamp())}",
            created_at=datetime.now()
        )
        db.add(topup_transaction)
        
        # Создаем транзакцию комиссии (5% от суммы)
        commission = amount * 0.05
        commission_transaction = DriverTransaction(
            driver_id=driver_id,
            type="commission",
            amount=-commission,
            description="Комиссия сервиса (5%)",
            status="completed",
            reference=f"COMM-{driver_id}-{int(datetime.now().timestamp())}",
            created_at=datetime.now()
        )
        db.add(commission_transaction)
        
        # Обновляем баланс водителя
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if driver:
            driver.balance = (driver.balance or 0.0) + amount - commission
        
        db.commit()
        print(f"✅ Созданы транзакции для водителя {driver_id}: пополнение +{amount}, комиссия -{commission}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания транзакций: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Пример использования
    create_topup_transaction(5, 1000.0, "Пополнение баланса диспетчером")
