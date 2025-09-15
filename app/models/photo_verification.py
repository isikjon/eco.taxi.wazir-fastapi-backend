from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base

class PhotoVerification(Base):
    __tablename__ = "photo_verifications"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    taxipark_id = Column(Integer, ForeignKey("taxiparks.id"), nullable=False)
    
    # Статус: pending, approved, rejected
    status = Column(String, default='pending', nullable=False)
    
    # Фотографии (JSON с путями к файлам)
    photos = Column(JSON, nullable=True)
    
    # Причина отклонения
    rejection_reason = Column(Text, nullable=True)
    
    # Кто обработал заявку
    processed_by = Column(String, nullable=True)  # имя диспетчера
    
    # Даты
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Связи
    driver = relationship("Driver", back_populates="photo_verifications")
    
    def __repr__(self):
        return f"<PhotoVerification(id={self.id}, driver_id={self.driver_id}, status={self.status})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "driver_id": self.driver_id,
            "driver_phone": self.driver.phone_number if self.driver else None,
            "driver_name": f"{self.driver.first_name} {self.driver.last_name}" if self.driver else None,
            "taxipark_id": self.taxipark_id,
            "status": self.status,
            "photos": self.photos,
            "rejection_reason": self.rejection_reason,
            "processed_by": self.processed_by,
            "submission_date": self.created_at.isoformat() if self.created_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }
