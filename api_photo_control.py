from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
import os
import uuid
from pathlib import Path

from app.database.session import get_db
from app.models.driver import Driver
from app.models.photo_verification import PhotoVerification
from pydantic import BaseModel
from sqlalchemy import desc

router = APIRouter(prefix="/api/photo-control", tags=["photo-control"])

# Pydantic модели
class PhotoSubmissionRequest(BaseModel):
    driver_phone: str
    photos: dict  # {"vu_front": "path", "vu_back": "path", "selfie": "path", etc.}

class PhotoVerificationResponse(BaseModel):
    id: int
    driver_phone: str
    driver_name: str
    submission_date: datetime
    status: str  # pending, approved, rejected
    photos: dict
    rejection_reason: Optional[str] = None

class ApprovalRequest(BaseModel):
    verification_id: int
    action: str  # approve, reject
    reason: Optional[str] = None

# Директория для сохранения фотографий
PHOTOS_DIR = Path("uploads/photos")
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

# Теперь используем базу данных вместо временного хранилища

@router.post("/submit", response_model=dict)
async def submit_photos_for_verification(
    driver_phone: str = Form(...),
    photos_json: Optional[str] = Form(None),
    selfie: Optional[UploadFile] = File(None),
    front: Optional[UploadFile] = File(None),
    back: Optional[UploadFile] = File(None),
    sts_front: Optional[UploadFile] = File(None),
    sts_back: Optional[UploadFile] = File(None),
    car_front: Optional[UploadFile] = File(None),
    car_left: Optional[UploadFile] = File(None),
    car_back: Optional[UploadFile] = File(None),
    car_right: Optional[UploadFile] = File(None),
    vin: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Отправка фотографий на проверку
    """
    try:
        # Проверяем существование водителя
        driver = db.query(Driver).filter(Driver.phone_number == driver_phone).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Водитель не найден")
        
        # Определяем формат данных (веб или мобильный)
        photos_data = {}
        
        if photos_json:
            # Веб-версия: получены blob-ссылки в JSON
            print("📸 Обрабатываем веб-запрос с JSON данными")
            try:
                photos_data = json.loads(photos_json)
                print(f"📸 Получены blob-ссылки: {list(photos_data.keys())}")
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Неверный формат JSON данных фотографий")
        else:
            # Мобильная версия: получены файлы
            print("📸 Обрабатываем мобильный запрос с файлами")
            uploaded_files = {
                'selfie': selfie,
                'front': front,
                'back': back,
                'sts_front': sts_front,
                'sts_back': sts_back,
                'car_front': car_front,
                'car_left': car_left,
                'car_back': car_back,
                'car_right': car_right,
                'vin': vin,
            }
            
            # Сохраняем файлы и создаем словарь путей
            for photo_type, file in uploaded_files.items():
                if file and file.filename:
                    try:
                        # Создаем уникальное имя файла (заменяем + на безопасный символ)
                        safe_phone = driver_phone.replace('+', '')
                        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
                        filename = f"{safe_phone}_{photo_type}_{uuid.uuid4().hex}.{file_extension}"
                        file_path = PHOTOS_DIR / filename
                        
                        # Сохраняем файл
                        with open(file_path, "wb") as buffer:
                            content = await file.read()
                            buffer.write(content)
                        
                        # Сохраняем относительный путь для веб-доступа
                        photos_data[photo_type] = f"/uploads/photos/{filename}"
                        print(f"📸 Сохранен файл {photo_type}: {file_path}")
                        
                    except Exception as e:
                        print(f"❌ Ошибка сохранения файла {photo_type}: {e}")
                        continue
        
        if not photos_data:
            raise HTTPException(status_code=400, detail="Не получено ни одного файла или данных фотографии")
        
        # Создаем заявку на фотоверификацию в БД
        new_verification = PhotoVerification(
            driver_id=driver.id,
            taxipark_id=driver.taxipark_id,
            status="pending",
            photos=photos_data
        )
        
        db.add(new_verification)
        
        # Обновляем статус фотоверификации водителя
        driver.photo_verification_status = "pending"
        
        db.commit()
        db.refresh(new_verification)
        
        print(f"📸 Получена заявка на фотоконтроль от {driver_phone}")
        print(f"📸 Фотографии: {list(photos_data.keys())}")
        print(f"📸 Пути к файлам: {photos_data}")
        
        return {
            "success": True,
            "message": "Фотографии отправлены на проверку",
            "verification_id": new_verification.id,
            "status": "pending"
        }
        
    except Exception as e:
        print(f"❌ Ошибка отправки фотографий: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка отправки фотографий: {str(e)}")

@router.get("/status", response_model=dict)
async def get_verification_status(
    driver_phone: str = Query(..., description="Номер телефона водителя"),
    db: Session = Depends(get_db)
):
    """
    Получение статуса проверки фотографий
    """
    try:
        # Находим водителя
        driver = db.query(Driver).filter(Driver.phone_number == driver_phone).first()
        if not driver:
            return {
                "status": "not_started",
                "rejection_reason": None
            }
        
        # Ищем последнюю заявку водителя из БД
        latest_verification = db.query(PhotoVerification).filter(
            PhotoVerification.driver_id == driver.id
        ).order_by(desc(PhotoVerification.created_at)).first()
        
        if not latest_verification:
            return {
                "status": driver.photo_verification_status,
                "rejection_reason": None
            }
        
        return {
            "status": latest_verification.status,
            "rejection_reason": latest_verification.rejection_reason,
            "submission_date": latest_verification.created_at.isoformat()
        }
        
    except Exception as e:
        print(f"❌ Ошибка получения статуса: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса: {str(e)}")

@router.get("/pending", response_model=List[PhotoVerificationResponse])
async def get_pending_verifications(
    taxipark_id: Optional[int] = Query(None, description="ID таксопарка"),
    db: Session = Depends(get_db)
):
    """
    Получение заявок на проверку для диспетчера
    """
    try:
        # Получаем заявки из БД
        query = db.query(PhotoVerification).filter(PhotoVerification.status == "pending")
        
        if taxipark_id:
            query = query.filter(PhotoVerification.taxipark_id == taxipark_id)
        
        verifications = query.order_by(desc(PhotoVerification.created_at)).all()
        
        pending_verifications = []
        for verification in verifications:
            pending_verifications.append(PhotoVerificationResponse(
                id=verification.id,
                driver_phone=verification.driver.phone_number,
                driver_name=f"{verification.driver.first_name} {verification.driver.last_name}",
                submission_date=verification.created_at,
                status=verification.status,
                photos=verification.photos or {},
                rejection_reason=verification.rejection_reason
            ))
        
        print(f"📋 Найдено {len(pending_verifications)} заявок на проверку")
        
        return pending_verifications
        
    except Exception as e:
        print(f"❌ Ошибка получения заявок: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения заявок: {str(e)}")

@router.post("/approve", response_model=dict)
async def approve_or_reject_verification(
    approval_data: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Одобрение или отклонение заявки на фотоконтроль
    """
    try:
        verification_id = approval_data.verification_id
        
        # Находим заявку в БД
        verification = db.query(PhotoVerification).filter(PhotoVerification.id == verification_id).first()
        
        if not verification:
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        
        if verification.status != "pending":
            raise HTTPException(status_code=400, detail="Заявка уже обработана")
        
        # Обновляем статус
        if approval_data.action == "approve":
            verification.status = "approved"
            verification.rejection_reason = None
            verification.processed_at = datetime.now()
            
            # Обновляем статус водителя в БД
            driver = verification.driver
            if driver:
                driver.is_active = True
                driver.photo_verification_status = "approved"
            
            message = "Заявка одобрена"
            
        elif approval_data.action == "reject":
            verification.status = "rejected"
            verification.rejection_reason = approval_data.reason or "Не указана причина"
            verification.processed_at = datetime.now()
            
            # Обновляем статус водителя в БД
            driver = verification.driver
            if driver:
                driver.is_active = False
                driver.photo_verification_status = "rejected"
            
            message = "Заявка отклонена"
            
        else:
            raise HTTPException(status_code=400, detail="Неверное действие")
        
        db.commit()
        
        print(f"✅ Заявка #{verification_id} {approval_data.action}: {driver.first_name} {driver.last_name}")
        if approval_data.reason:
            print(f"📝 Причина: {approval_data.reason}")
        
        return {
            "success": True,
            "message": message,
            "verification_id": verification_id,
            "new_status": verification.status
        }
        
    except Exception as e:
        print(f"❌ Ошибка обработки заявки: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки заявки: {str(e)}")

@router.get("/verification/{verification_id}")
async def get_verification_details(
    verification_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение деталей конкретной заявки
    """
    try:
        # Находим заявку в БД
        verification = db.query(PhotoVerification).filter(PhotoVerification.id == verification_id).first()
        
        if not verification:
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        
        return {
            "id": verification.id,
            "driver_phone": verification.driver.phone_number,
            "driver_name": f"{verification.driver.first_name} {verification.driver.last_name}",
            "created_at": verification.created_at.isoformat(),
            "status": verification.status,
            "photos": verification.photos or {},
            "rejection_reason": verification.rejection_reason
        }
        
    except Exception as e:
        print(f"❌ Ошибка получения деталей: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения деталей: {str(e)}")

@router.get("/stats", response_model=dict)
async def get_photo_control_stats(
    taxipark_id: Optional[int] = Query(None, description="ID таксопарка"),
    db: Session = Depends(get_db)
):
    """
    Статистика по фотоконтролю
    """
    try:
        # Получаем статистику из БД
        query = db.query(PhotoVerification)
        
        if taxipark_id:
            query = query.filter(PhotoVerification.taxipark_id == taxipark_id)
        
        total = query.count()
        pending = query.filter(PhotoVerification.status == "pending").count()
        approved = query.filter(PhotoVerification.status == "approved").count()
        rejected = query.filter(PhotoVerification.status == "rejected").count()
        
        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected
        }
        
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")

@router.post("/upload-single", response_model=dict)
async def upload_single_photo(
    driver_phone: str = Form(...),
    photo_type: str = Form(...),
    filename: str = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Загрузка одиночного фото (для веб-версии)
    """
    try:
        # Проверяем существование водителя
        driver = db.query(Driver).filter(Driver.phone_number == driver_phone).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Водитель не найден")
        
        # Создаем путь к файлу
        file_path = PHOTOS_DIR / filename
        
        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            content = await photo.read()
            buffer.write(content)
        
        print(f"📸 Загружен файл {photo_type}: {file_path}")
        
        return {
            "success": True,
            "message": "Файл успешно загружен",
            "filename": filename,
            "photo_type": photo_type
        }
        
    except Exception as e:
        print(f"❌ Ошибка загрузки файла: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки файла: {str(e)}")

@router.delete("/clear-all", response_model=dict)
async def clear_all_verifications(db: Session = Depends(get_db)):
    """
    Очистка всех заявок на фотоконтроль (для отладки)
    """
    count = db.query(PhotoVerification).count()
    db.query(PhotoVerification).delete()
    db.commit()
    
    print(f"🗑️ Очищено {count} заявок на фотоконтроль")
    
    return {
        "success": True,
        "message": f"Очищено {count} заявок",
        "cleared_count": count
    }
