from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.taxipark import TaxiPark
from app.models.driver import Driver
from app.models.order import Order
from app.models.administrator import Administrator

class DispatcherService:
    
    @staticmethod
    def get_taxipark_balance(db: Session, taxipark_id: int) -> float:
        """Получить баланс таксопарка"""
        taxipark = db.query(TaxiPark).filter(TaxiPark.id == taxipark_id).first()
        if taxipark:
            return taxipark.balance if hasattr(taxipark, 'balance') else 0.0
        return 0.0
    
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
