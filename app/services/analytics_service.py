from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.order import Order
from app.models.driver import Driver
from app.models.superadmin import SuperAdmin
from datetime import datetime, timedelta
from typing import Dict, Any

class AnalyticsService:
    
    @staticmethod
    def get_dashboard_stats(db: Session, days: int = 7) -> Dict[str, Any]:
        """Получить статистику для дашборда за указанное количество дней"""
        
        # Для dashboard показываем общую статистику за все время
        # Заказы за все время (все статусы кроме отмененных)
        orders_query = db.query(Order).filter(Order.status != "cancelled")
        
        completed_orders = orders_query.count()
        total_earnings = orders_query.with_entities(func.sum(Order.price)).scalar() or 0.0
        
        # Водители
        total_drivers = db.query(Driver).filter(Driver.is_active == True).count()
        
        # Пополнения водителей (симуляция - считаем водителей с балансом > 0)
        driver_topups = db.query(Driver).filter(Driver.balance > 0).count()
        
        # Суперадмины
        total_superadmins = db.query(SuperAdmin).filter(SuperAdmin.is_active == True).count()
        
        return {
            "orders_completed": int(completed_orders),  # Гарантируем int
            "total_earnings": float(total_earnings),   # Гарантируем float
            "driver_topups": int(driver_topups),       # Гарантируем int
            "total_superadmins": int(total_superadmins), # Гарантируем int
            "period_days": int(days)
        }
    
    @staticmethod
    def get_orders_stats(db: Session, days: int = 7) -> Dict[str, Any]:
        """Получить статистику по заказам"""
        start_date = datetime.now() - timedelta(days=days)
        
        orders = db.query(Order).filter(
            and_(
                Order.created_at >= start_date,
                Order.status == "completed"
            )
        ).all()
        
        total_orders = len(orders)
        total_earnings = sum(order.price for order in orders) if orders else 0
        avg_order_price = total_earnings / total_orders if total_orders > 0 else 0
        
        return {
            "total_orders": int(total_orders),
            "total_earnings": float(total_earnings),
            "avg_order_price": float(avg_order_price),
            "period_days": int(days)
        }
    
    @staticmethod
    def get_drivers_stats(db: Session) -> Dict[str, Any]:
        """Получить статистику по водителям"""
        total_drivers = db.query(Driver).count()
        active_drivers = db.query(Driver).filter(Driver.is_active == True).count()
        total_balance = db.query(func.sum(Driver.balance)).scalar() or 0.0
        
        return {
            "total_drivers": int(total_drivers),
            "active_drivers": int(active_drivers),
            "inactive_drivers": int(total_drivers - active_drivers),
            "total_balance": float(total_balance)
        }
    
    @staticmethod
    def get_superadmins_stats(db: Session) -> Dict[str, Any]:
        """Получить статистику по суперадминам"""
        total_superadmins = db.query(SuperAdmin).count()
        active_superadmins = db.query(SuperAdmin).filter(SuperAdmin.is_active == True).count()
        
        return {
            "total_superadmins": int(total_superadmins),
            "active_superadmins": int(active_superadmins),
            "inactive_superadmins": int(total_superadmins - active_superadmins)
        }
