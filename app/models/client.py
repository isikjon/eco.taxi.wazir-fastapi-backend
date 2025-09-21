from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.sql import func
from app.database.session import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), nullable=True)
    rating = Column(Float, default=5.0)
    total_rides = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    preferred_payment_method = Column(String(20), default='cash')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Client(id={self.id}, name={self.first_name} {self.last_name}, phone={self.phone_number})>"

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone_number": self.phone_number,
            "email": self.email,
            "rating": self.rating,
            "total_rides": self.total_rides,
            "total_spent": self.total_spent,
            "preferred_payment_method": self.preferred_payment_method,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
