from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base

class DriverTransaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    type = Column(String(50), nullable=False)  # topup, order, commission, withdrawal, bonus
    amount = Column(Float, nullable=False)
    description = Column(Text)
    status = Column(String(20), default="completed")  # completed, pending, failed
    reference = Column(String(100))  # Уникальный номер транзакции
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Связь с водителем
    driver = relationship("Driver")
