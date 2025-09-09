from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    car_model = Column(String, nullable=False)
    car_number = Column(String, unique=True, nullable=False)
    balance = Column(Float, default=0.0)
    tariff = Column(String, default='Эконом')  # Эконом, Комфорт, Бизнес
    taxipark_id = Column(Integer, ForeignKey("taxiparks.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    orders = relationship("Order", back_populates="driver")

    def __repr__(self):
        return f"<Driver(id={self.id}, name={self.first_name} {self.last_name}, balance={self.balance})>"

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "car_model": self.car_model,
            "car_number": self.car_number,
            "balance": self.balance,
            "tariff": self.tariff,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
