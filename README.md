# Taxi Driver Registration API

FastAPI backend для регистрации и авторизации водителей такси.

## Установка и запуск

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Запуск сервера
```bash
python start_server.py
```

Или вручную:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Доступ к API
- **Сервер**: http://localhost:8000
- **Документация**: http://localhost:8000/docs
- **OpenAPI схема**: http://localhost:8000/openapi.json

## API Endpoints

### 1. Получить список таксопарков
```http
GET /api/parks
```

**Ответ:**
```json
{
  "parks": [
    {
      "id": 1,
      "name": "ООО Платинум Партнер",
      "city": "Ош",
      "phone": "+970667788778",
      "email": "example@gmail.com",
      "address": "Кыргызстан г. Ок мкр Анар 1",
      "working_hours": "Пн-Сб 10:00-18:00\nВс-выходной",
      "commission_percent": 15,
      "description": "Надежный партнер с многолетним опытом работы"
    }
  ],
  "count": 4
}
```

### 2. Отправить SMS код
```http
POST /api/sms/send
```

**Тело запроса:**
```json
{
  "phoneNumber": "+996700123456"
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "SMS код отправлен",
  "test_code": "1111"
}
```

### 3. Авторизация водителя
```http
POST /api/drivers/login
```

**Тело запроса:**
```json
{
  "phoneNumber": "+996700123456",
  "smsCode": "1111"
}
```

**Ответ для нового пользователя:**
```json
{
  "success": true,
  "isNewUser": true,
  "message": "Новый пользователь, требуется регистрация"
}
```

**Ответ для существующего пользователя:**
```json
{
  "success": true,
  "isNewUser": false,
  "driver": {
    "id": 1,
    "phoneNumber": "+996700123456",
    "fullName": "Иван Иванов",
    "status": "registered"
  }
}
```

### 4. Регистрация водителя
```http
POST /api/drivers/register
```

**Тело запроса:**
```json
{
  "user": {
    "phoneNumber": "+996700123456",
    "city": "Ош",
    "fullName": "Иван Иванов",
    "country": "Кыргызстан",
    "licenseNumber": "AB 12 345678",
    "issueDate": "01.01.2020",
    "expiryDate": "01.01.2030",
    "invitationCode": "123456"
  },
  "car": {
    "brand": "Toyota",
    "model": "Camry",
    "color": "Белый",
    "year": "2020",
    "licensePlate": "01 KG H 1234"
  },
  "park": {
    "id": 1,
    "name": "ООО Платинум Партнер"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Водитель успешно зарегистрирован",
  "driver_id": 1,
  "status": "registered"
}
```

### 5. Проверить статус водителя
```http
GET /api/drivers/status?phoneNumber=+996700123456
```

**Ответ:**
```json
{
  "exists": true,
  "driver": {
    "id": 1,
    "phoneNumber": "+996700123456",
    "fullName": "Иван Иванов",
    "status": "registered",
    "registeredAt": "2024-01-01 12:00:00"
  }
}
```

## База данных

API автоматически создает SQLite базу данных `taxi_admin.db` со следующими таблицами:

### parks
- id (PRIMARY KEY)
- name (TEXT)
- city (TEXT) 
- phone (TEXT)
- email (TEXT)
- address (TEXT)
- working_hours (TEXT)
- commission_percent (INTEGER)
- description (TEXT)
- created_at (TIMESTAMP)

### drivers
- id (PRIMARY KEY)
- phone_number (TEXT UNIQUE)
- full_name (TEXT)
- city (TEXT)
- country (TEXT)
- license_number (TEXT)
- issue_date (TEXT)
- expiry_date (TEXT)
- invitation_code (TEXT)
- car_brand (TEXT)
- car_model (TEXT)
- car_color (TEXT)
- car_year (TEXT)
- license_plate (TEXT)
- park_id (INTEGER FOREIGN KEY)
- status (TEXT DEFAULT 'pending')
- registration_data (TEXT JSON)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

### sms_codes
- id (PRIMARY KEY)
- phone_number (TEXT)
- code (TEXT)
- expires_at (TIMESTAMP)
- used (BOOLEAN DEFAULT FALSE)
- created_at (TIMESTAMP)

## Тестирование

Для тестирования используйте:
- **SMS код**: `1111` (работает для всех номеров)
- **Документация API**: http://localhost:8000/docs

## Разработка

Для разработки запустите сервер с автоперезагрузкой:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```