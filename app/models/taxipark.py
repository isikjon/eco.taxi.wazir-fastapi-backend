from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base


class TaxiPark(Base):
    __tablename__ = "taxiparks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    city = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    working_hours = Column(String(255), nullable=True)
    description = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    income = Column(Float, default=0.0)
    balance = Column(Float, default=0.0)
    drivers_count = Column(Integer, default=0)
    dispatchers_count = Column(Integer, default=0)
    commission_percent = Column(Float, default=15.0)  # По умолчанию 15%
    is_active = Column(Boolean, default=True)
    
    # Связи
    administrators = relationship("Administrator", back_populates="taxipark")
    drivers = relationship("Driver", back_populates="taxipark")
    
    def __repr__(self):
        return f"<TaxiPark(id={self.id}, name='{self.name}', commission={self.commission_percent}%)>"
