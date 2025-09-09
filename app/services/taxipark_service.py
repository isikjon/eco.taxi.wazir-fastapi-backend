from sqlalchemy.orm import Session
from app.models.taxipark import TaxiPark
from app.schemas.taxipark import TaxiParkCreate, TaxiParkUpdate
from typing import List, Optional


class TaxiParkService:
    
    @staticmethod
    def create_taxipark(db: Session, taxipark_data: TaxiParkCreate) -> TaxiPark:
        """Создать новый таксопарк"""
        db_taxipark = TaxiPark(**taxipark_data.model_dump())
        db.add(db_taxipark)
        db.commit()
        db.refresh(db_taxipark)
        return db_taxipark
    
    @staticmethod
    def get_taxipark(db: Session, taxipark_id: int) -> Optional[TaxiPark]:
        """Получить таксопарк по ID"""
        return db.query(TaxiPark).filter(TaxiPark.id == taxipark_id).first()
    
    @staticmethod
    def get_taxiparks(db: Session, skip: int = 0, limit: int = 100) -> List[TaxiPark]:
        """Получить список таксопарков"""
        return db.query(TaxiPark).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_taxipark(db: Session, taxipark_id: int, taxipark_data: TaxiParkUpdate) -> Optional[TaxiPark]:
        """Обновить таксопарк"""
        db_taxipark = TaxiParkService.get_taxipark(db, taxipark_id)
        if not db_taxipark:
            return None
        
        update_data = taxipark_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_taxipark, field, value)
        
        db.commit()
        db.refresh(db_taxipark)
        return db_taxipark
    
    @staticmethod
    def delete_taxipark(db: Session, taxipark_id: int) -> bool:
        """Удалить таксопарк"""
        db_taxipark = TaxiParkService.get_taxipark(db, taxipark_id)
        if not db_taxipark:
            return False
        
        db.delete(db_taxipark)
        db.commit()
        return True
    
    @staticmethod
    def get_taxipark_count(db: Session) -> int:
        """Получить количество таксопарков"""
        return db.query(TaxiPark).count()
    
    @staticmethod
    def update_commission(db: Session, taxipark_id: int, commission_percent: float) -> Optional[TaxiPark]:
        """Обновить процент комиссии"""
        return TaxiParkService.update_taxipark(
            db, 
            taxipark_id, 
            TaxiParkUpdate(commission_percent=commission_percent)
        )
