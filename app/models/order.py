from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, nullable=False)
    client_phone = Column(String, nullable=False)
    pickup_address = Column(String, nullable=False)
    destination_address = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String, default="completed")  # completed, cancelled, in_progress
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Связи
    driver = relationship("Driver", back_populates="orders")

    def __repr__(self):
        return f"<Order(id={self.id}, price={self.price}, status={self.status})>"

    def to_dict(self):
        return {
            "id": self.id,
            "client_name": self.client_name,
            "client_phone": self.client_phone,
            "pickup_address": self.pickup_address,
            "destination_address": self.destination_address,
            "price": self.price,
            "status": self.status,
            "driver_id": self.driver_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
