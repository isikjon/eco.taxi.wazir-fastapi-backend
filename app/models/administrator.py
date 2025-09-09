from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base


class Administrator(Base):
    __tablename__ = "administrators"
    
    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    taxipark_id = Column(Integer, ForeignKey("taxiparks.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Связь с таксопарком
    taxipark = relationship("TaxiPark", back_populates="administrators")
    
    def __repr__(self):
        return f"<Administrator(id={self.id}, login='{self.login}', name='{self.first_name} {self.last_name}')>"
