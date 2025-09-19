from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, nullable=False)  # Уникальный номер заказа
    
    # Информация о клиенте
    client_name = Column(String, nullable=True)
    client_phone = Column(String, nullable=True)
    
    # Адреса с координатами
    pickup_address = Column(String, nullable=False)
    pickup_latitude = Column(Float, nullable=True)
    pickup_longitude = Column(Float, nullable=True)
    
    destination_address = Column(String, nullable=False)
    destination_latitude = Column(Float, nullable=True)
    destination_longitude = Column(Float, nullable=True)
    
    # Информация о заказе
    price = Column(Float, default=0.0)
    distance = Column(Float, nullable=True)  # Расстояние в км
    duration = Column(Integer, nullable=True)  # Время в минутах
    
    # Статусы заказа
    status = Column(String, default="received")  # received, accepted, navigating_to_a, arrived_at_a, navigating_to_b, completed, cancelled
    
    # Водитель и таксопарк
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    taxipark_id = Column(Integer, ForeignKey("taxiparks.id"), nullable=False)
    
    # Тариф и оплата
    tariff = Column(String, nullable=True)  # Эконом, Комфорт, Бизнес
    payment_method = Column(String, nullable=True)  # cash, card, online
    
    # Примечания
    notes = Column(Text, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    arrived_at_a = Column(DateTime(timezone=True), nullable=True)
    started_to_b = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Связи
    driver = relationship("Driver", back_populates="orders")

    def __repr__(self):
        return f"<Order(id={self.id}, order_number={self.order_number}, status={self.status})>"

    def get_status_display(self):
        """Получить статус на русском языке"""
        status_map = {
            'received': 'Получен',
            'accepted': 'Принят',
            'navigating_to_a': 'Едет к точке А',
            'arrived_at_a': 'Прибыл в точку А',
            'navigating_to_b': 'Едет к точке Б',
            'completed': 'Выполнен',
            'cancelled': 'Отменен',
            'in_progress': 'Выполняется'
        }
        return status_map.get(self.status, self.status)

    def get_driver_display_name(self):
        """Получить отображаемое имя водителя (позывной или ФИО)"""
        if not self.driver:
            return "Не назначен"
        
        # Если есть позывной, используем его
        if self.driver.call_sign and self.driver.call_sign.strip():
            return self.driver.call_sign.strip()
        
        # Иначе используем ФИО
        return f"{self.driver.first_name} {self.driver.last_name}".strip()

    def to_dict(self):
        return {
            "id": self.id,
            "order_number": self.order_number,
            "client_name": self.client_name,
            "client_phone": self.client_phone,
            "pickup_address": self.pickup_address,
            "pickup_latitude": self.pickup_latitude,
            "pickup_longitude": self.pickup_longitude,
            "destination_address": self.destination_address,
            "destination_latitude": self.destination_latitude,
            "destination_longitude": self.destination_longitude,
            "price": self.price,
            "distance": self.distance,
            "duration": self.duration,
            "status": self.status,
            "status_display": self.get_status_display(),
            "driver_id": self.driver_id,
            "driver_name": f"{self.driver.first_name} {self.driver.last_name}" if self.driver else None,
            "driver_display_name": self.get_driver_display_name(),
            "driver_phone": self.driver.phone_number if self.driver else None,
            "tariff": self.tariff,
            "payment_method": self.payment_method,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "arrived_at_a": self.arrived_at_a.isoformat() if self.arrived_at_a else None,
            "started_to_b": self.started_to_b.isoformat() if self.started_to_b else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None
        }
