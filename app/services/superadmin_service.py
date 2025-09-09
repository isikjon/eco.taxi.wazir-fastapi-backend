from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.superadmin import SuperAdmin
from app.schemas.superadmin import SuperAdminCreate, SuperAdminUpdate
from app.core.security import get_password_hash
from typing import List, Optional

class SuperAdminService:
    
    @staticmethod
    def create_superadmin(db: Session, superadmin_data: SuperAdminCreate) -> SuperAdmin:
        """Создать нового суперадмина"""
        # Проверяем, что логин уникален
        existing_admin = db.query(SuperAdmin).filter(SuperAdmin.login == superadmin_data.login).first()
        if existing_admin:
            raise ValueError(f"Суперадмин с логином '{superadmin_data.login}' уже существует")
        
        # Хешируем пароль
        hashed_password = get_password_hash(superadmin_data.password)
        
        # Создаем нового суперадмина
        db_superadmin = SuperAdmin(
            login=superadmin_data.login,
            hashed_password=hashed_password,
            position=superadmin_data.position
        )
        
        db.add(db_superadmin)
        db.commit()
        db.refresh(db_superadmin)
        
        return db_superadmin
    
    @staticmethod
    def get_superadmin(db: Session, superadmin_id: int) -> Optional[SuperAdmin]:
        """Получить суперадмина по ID"""
        return db.query(SuperAdmin).filter(SuperAdmin.id == superadmin_id).first()
    
    @staticmethod
    def get_superadmin_by_login(db: Session, login: str) -> Optional[SuperAdmin]:
        """Получить суперадмина по логину"""
        return db.query(SuperAdmin).filter(SuperAdmin.login == login).first()
    
    @staticmethod
    def get_superadmins(db: Session, skip: int = 0, limit: int = 100) -> List[SuperAdmin]:
        """Получить список суперадминов"""
        return db.query(SuperAdmin).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_superadmin(db: Session, superadmin_id: int, superadmin_data: SuperAdminUpdate) -> Optional[SuperAdmin]:
        """Обновить суперадмина"""
        db_superadmin = db.query(SuperAdmin).filter(SuperAdmin.id == superadmin_id).first()
        if not db_superadmin:
            return None
        
        # Обновляем только переданные поля
        update_data = superadmin_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_superadmin, field, value)
        
        db.commit()
        db.refresh(db_superadmin)
        
        return db_superadmin
    
    @staticmethod
    def delete_superadmin(db: Session, superadmin_id: int) -> bool:
        """Удалить суперадмина"""
        db_superadmin = db.query(SuperAdmin).filter(SuperAdmin.id == superadmin_id).first()
        if not db_superadmin:
            return False
        
        db.delete(db_superadmin)
        db.commit()
        
        return True
    
    @staticmethod
    def get_superadmin_count(db: Session) -> int:
        """Получить количество суперадминов"""
        return db.query(SuperAdmin).count()
