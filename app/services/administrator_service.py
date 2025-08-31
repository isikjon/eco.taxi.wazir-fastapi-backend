from sqlalchemy.orm import Session
from app.models.administrator import Administrator
from app.models.taxipark import TaxiPark
from app.schemas.administrator import AdministratorCreate, AdministratorUpdate
from app.core.security import get_password_hash
from typing import List, Optional


class AdministratorService:
    
    @staticmethod
    def create_administrator(db: Session, administrator_data: AdministratorCreate) -> Administrator:
        """Создать нового администратора"""
        hashed_password = get_password_hash(administrator_data.password)
        
        db_administrator = Administrator(
            login=administrator_data.login,
            hashed_password=hashed_password,
            first_name=administrator_data.first_name,
            last_name=administrator_data.last_name,
            taxipark_id=administrator_data.taxipark_id
        )
        
        db.add(db_administrator)
        db.commit()
        db.refresh(db_administrator)
        
        # Обновляем количество администраторов в таксопарке
        AdministratorService._update_taxipark_admin_count(db, administrator_data.taxipark_id)
        
        return db_administrator
    
    @staticmethod
    def get_administrator(db: Session, administrator_id: int) -> Optional[Administrator]:
        """Получить администратора по ID"""
        return db.query(Administrator).filter(Administrator.id == administrator_id).first()
    
    @staticmethod
    def get_administrators(db: Session, skip: int = 0, limit: int = 100, taxipark_id: Optional[int] = None) -> List[Administrator]:
        """Получить список администраторов с возможностью фильтрации по таксопарку"""
        query = db.query(Administrator)
        
        if taxipark_id is not None:
            query = query.filter(Administrator.taxipark_id == taxipark_id)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_administrators_with_taxipark_info(db: Session, taxipark_id: Optional[int] = None) -> List[dict]:
        """Получить список администраторов с информацией о таксопарке"""
        query = db.query(
            Administrator,
            TaxiPark.name.label('taxipark_name')
        ).join(TaxiPark, Administrator.taxipark_id == TaxiPark.id)
        
        if taxipark_id is not None:
            query = query.filter(Administrator.taxipark_id == taxipark_id)
        
        results = query.all()
        
        administrators = []
        for admin, taxipark_name in results:
            admin_dict = {
                'id': admin.id,
                'login': admin.login,
                'first_name': admin.first_name,
                'last_name': admin.last_name,
                'taxipark_id': admin.taxipark_id,
                'taxipark_name': taxipark_name,
                'is_active': admin.is_active,
                'created_at': admin.created_at
            }
            administrators.append(admin_dict)
        
        return administrators
    
    @staticmethod
    def update_administrator(db: Session, administrator_id: int, administrator_data: AdministratorUpdate) -> Optional[Administrator]:
        """Обновить администратора"""
        db_administrator = AdministratorService.get_administrator(db, administrator_id)
        if not db_administrator:
            return None
        
        old_taxipark_id = db_administrator.taxipark_id
        
        update_data = administrator_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_administrator, field, value)
        
        db.commit()
        db.refresh(db_administrator)
        
        # Обновляем количество администраторов в старом и новом таксопарке
        if old_taxipark_id != db_administrator.taxipark_id:
            AdministratorService._update_taxipark_admin_count(db, old_taxipark_id)
            AdministratorService._update_taxipark_admin_count(db, db_administrator.taxipark_id)
        
        return db_administrator
    
    @staticmethod
    def delete_administrator(db: Session, administrator_id: int) -> bool:
        """Удалить администратора"""
        db_administrator = AdministratorService.get_administrator(db, administrator_id)
        if not db_administrator:
            return False
        
        taxipark_id = db_administrator.taxipark_id
        
        db.delete(db_administrator)
        db.commit()
        
        # Обновляем количество администраторов в таксопарке
        AdministratorService._update_taxipark_admin_count(db, taxipark_id)
        
        return True
    
    @staticmethod
    def toggle_administrator_status(db: Session, administrator_id: int) -> Optional[Administrator]:
        """Переключить статус администратора (активен/заблокирован)"""
        db_administrator = AdministratorService.get_administrator(db, administrator_id)
        if not db_administrator:
            return None
        
        db_administrator.is_active = not db_administrator.is_active
        db.commit()
        db.refresh(db_administrator)
        
        return db_administrator
    
    @staticmethod
    def get_administrator_count(db: Session, taxipark_id: Optional[int] = None) -> int:
        """Получить количество администраторов"""
        query = db.query(Administrator)
        
        if taxipark_id is not None:
            query = query.filter(Administrator.taxipark_id == taxipark_id)
        
        return query.count()
    
    @staticmethod
    def _update_taxipark_admin_count(db: Session, taxipark_id: int):
        """Обновить количество администраторов в таксопарке"""
        count = db.query(Administrator).filter(Administrator.taxipark_id == taxipark_id).count()
        
        taxipark = db.query(TaxiPark).filter(TaxiPark.id == taxipark_id).first()
        if taxipark:
            taxipark.dispatchers_count = count
            db.commit()
