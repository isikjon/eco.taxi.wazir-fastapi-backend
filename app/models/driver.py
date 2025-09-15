from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone_number = Column(String, unique=True, nullable=False)
    car_model = Column(String, nullable=False)
    car_number = Column(String, unique=True, nullable=False)
    car_color = Column(String, nullable=True)
    car_year = Column(String, nullable=True)
    car_vin = Column(String, nullable=True)
    car_body_number = Column(String, nullable=True)
    car_sts = Column(String, nullable=True)
    call_sign = Column(String, nullable=True)
    balance = Column(Float, default=0.0)
    tariff = Column(String, default='Эконом')  # Эконом, Комфорт, Бизнес
    taxipark_id = Column(Integer, ForeignKey("taxiparks.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Статус фотоверификации: not_started, pending, approved, rejected
    photo_verification_status = Column(String, default='not_started', nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    orders = relationship("Order", back_populates="driver")
    taxipark = relationship("TaxiPark", back_populates="drivers")
    photo_verifications = relationship("PhotoVerification", back_populates="driver")

    def __repr__(self):
        return f"<Driver(id={self.id}, name={self.first_name} {self.last_name}, balance={self.balance})>"

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone_number": self.phone_number,
            "car_model": self.car_model,
            "car_number": self.car_number,
            "car_color": self.car_color,
            "car_year": self.car_year,
            "car_vin": self.car_vin,
            "car_body_number": self.car_body_number,
            "car_sts": self.car_sts,
            "call_sign": self.call_sign,
            "balance": self.balance,
            "tariff": self.tariff,
            "is_active": self.is_active,
            "photo_verification_status": self.photo_verification_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
