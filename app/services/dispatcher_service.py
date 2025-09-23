from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.taxipark import TaxiPark
from app.models.driver import Driver
from app.models.order import Order
from app.models.administrator import Administrator

class DispatcherService:
    
    @staticmethod
    def get_taxipark_balance(db: Session, taxipark_id: int) -> float:
        """Получить общий баланс всех водителей таксопарка"""
        from sqlalchemy import func
        
        # Считаем сумму балансов всех водителей в таксопарке
        total_balance = db.query(func.sum(Driver.balance)).filter(
            Driver.taxipark_id == taxipark_id
        ).scalar()
        
        # Отладочная информация
        drivers_with_balance = db.query(Driver).filter(
            Driver.taxipark_id == taxipark_id
        ).all()
        
        print(f"🔍 DEBUG: Calculating total balance for taxipark {taxipark_id}")
        individual_balances = []
        for driver in drivers_with_balance:
            balance = driver.balance if driver.balance else 0
            individual_balances.append(balance)
            print(f"🔍 DEBUG: Driver {driver.first_name} {driver.last_name}: {balance}")
        
        calculated_total = sum(individual_balances)
        print(f"🔍 DEBUG: Individual balances: {individual_balances}")
        print(f"🔍 DEBUG: SQL sum result: {total_balance}")
        print(f"🔍 DEBUG: Calculated total: {calculated_total}")
        
        return float(total_balance) if total_balance is not None else 0.0
    
    @staticmethod
    def get_drivers_count(db: Session, taxipark_id: int) -> int:
        """Получить количество водителей в таксопарке"""
        return db.query(Driver).filter(Driver.taxipark_id == taxipark_id).count()
    
    @staticmethod
    def get_orders(db: Session, taxipark_id: int, limit: int = 50) -> List[Order]:
        """Получить заказы таксопарка"""
        from sqlalchemy.orm import joinedload
        return db.query(Order).options(joinedload(Order.driver)).filter(Order.taxipark_id == taxipark_id).order_by(Order.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_orders_count_by_status(db: Session, taxipark_id: int) -> dict:
        """Получить количество заказов по статусам"""
        total = db.query(Order).filter(Order.taxipark_id == taxipark_id).count()
        completed = db.query(Order).filter(Order.taxipark_id == taxipark_id, Order.status == "completed").count()
        cancelled = db.query(Order).filter(Order.taxipark_id == taxipark_id, Order.status == "cancelled").count()
        in_progress = db.query(Order).filter(Order.taxipark_id == taxipark_id, Order.status == "in_progress").count()
        
        return {
            "total": total,
            "completed": completed,
            "cancelled": cancelled,
            "in_progress": in_progress
        }
    
    @staticmethod
    def get_total_topups_count(db: Session, taxipark_id: int) -> int:
        """Получить общее количество пополнений баланса"""
        from app.models.transaction import DriverTransaction
        
        # Сначала посмотрим, есть ли вообще транзакции в базе
        all_transactions_count = db.query(DriverTransaction).count()
        print(f"🔍 DEBUG: Total transactions in database: {all_transactions_count}")
        
        # Посмотрим, какие типы транзакций есть
        all_types = db.query(DriverTransaction.type).distinct().all()
        print(f"🔍 DEBUG: All transaction types: {[t[0] for t in all_types]}")
        
        # Считаем все транзакции типа 'topup' для водителей данного таксопарка
        total_topups = db.query(DriverTransaction).join(Driver).filter(
            Driver.taxipark_id == taxipark_id,
            DriverTransaction.type == 'topup'
        ).count()
        
        print(f"🔍 DEBUG: Total topups for taxipark {taxipark_id}: {total_topups}")
        
        # Если нет пополнений, но есть другие транзакции, покажем их
        if total_topups == 0 and all_transactions_count > 0:
            all_taxipark_transactions = db.query(DriverTransaction).join(Driver).filter(
                Driver.taxipark_id == taxipark_id
            ).count()
            print(f"🔍 DEBUG: Total transactions for taxipark {taxipark_id}: {all_taxipark_transactions}")
        
        return total_topups
    
    @staticmethod
    def get_topup_history(db: Session, taxipark_id: int, limit: int = 50) -> List:
        """Получить историю пополнений баланса"""
        from app.models.transaction import DriverTransaction
        from sqlalchemy.orm import joinedload
        
        # Получаем все пополнения для водителей данного таксопарка
        topups = db.query(DriverTransaction).join(Driver).options(
            joinedload(DriverTransaction.driver)
        ).filter(
            Driver.taxipark_id == taxipark_id,
            DriverTransaction.type == 'topup'
        ).order_by(DriverTransaction.created_at.desc()).limit(limit).all()
        
        print(f"🔍 DEBUG: Retrieved {len(topups)} topup transactions for taxipark {taxipark_id}")
        
        return topups
    
    @staticmethod
    def get_dispatcher_stats(db: Session, taxipark_id: int) -> dict:
        """Получить статистику для диспетчерской"""
        balance = DispatcherService.get_taxipark_balance(db, taxipark_id)
        drivers_count = DispatcherService.get_drivers_count(db, taxipark_id)
        orders_stats = DispatcherService.get_orders_count_by_status(db, taxipark_id)
        orders = DispatcherService.get_orders(db, taxipark_id)
        
        return {
            "balance": balance,
            "drivers_count": drivers_count,
            "orders_stats": orders_stats,
            "orders": orders
        }
