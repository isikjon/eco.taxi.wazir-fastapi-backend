import json
import os
from typing import Optional, Dict, Any
from app.core.config import settings

try:
    from firebase_admin import credentials, messaging, initialize_app
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️ Firebase Admin SDK не установлен. Установите: pip install firebase-admin")

class FCMService:
    def __init__(self):
        print("🔍 [FCM] Инициализация FCM сервиса...")
        self.project_id = "eco-taxi-driver-b715f"
        self.sender_id = "1004431092746"
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        print("🔍 [FCM] Начинаем инициализацию Firebase...")
        print(f"🔍 [FCM] Firebase доступен: {FIREBASE_AVAILABLE}")
        
        if not FIREBASE_AVAILABLE:
            print("❌ [FCM] Firebase Admin SDK недоступен")
            return
            
        try:
            service_account_path = settings.FCM_SERVICE_ACCOUNT_PATH
            print(f"🔍 [FCM] Путь к сервисному аккаунту: {service_account_path}")
            
            if not os.path.exists(service_account_path):
                print(f"❌ [FCM] Файл сервисного аккаунта не найден: {service_account_path}")
                return
            
            print("🔍 [FCM] Загружаем сертификат...")
            cred = credentials.Certificate(service_account_path)
            print("🔍 [FCM] Инициализируем Firebase приложение...")
            initialize_app(cred)
            print("✅ [FCM] Firebase Admin SDK инициализирован успешно")
        except Exception as e:
            print(f"❌ [FCM] Ошибка инициализации Firebase Admin SDK: {e}")
            import traceback
            print(f"❌ [FCM] Stack trace: {traceback.format_exc()}")
    
    def send_notification(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Отправка push-уведомления через Firebase Admin SDK
        """
        print(f"🔍 [FCM] Начинаем отправку уведомления")
        print(f"🔍 [FCM] Токен: {fcm_token[:20] if fcm_token else 'None'}...")
        print(f"🔍 [FCM] Заголовок: {title}")
        print(f"🔍 [FCM] Текст: {body}")
        print(f"🔍 [FCM] Данные: {data}")
        
        if not FIREBASE_AVAILABLE:
            print("❌ [FCM] Firebase Admin SDK недоступен")
            return False

        if not fcm_token:
            print("❌ [FCM] FCM токен отсутствует")
            return False

        try:
            print(f"🔍 [FCM] Создаем сообщение...")
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        vibrate_timings_millis=[200, 100, 200],
                    ),
                ),
            )
            print(f"🔍 [FCM] Сообщение создано успешно")

            print(f"🔍 [FCM] Отправляем сообщение через Firebase...")
            response = messaging.send(message)
            print(f"✅ [FCM] FCM уведомление отправлено: {title} (ID: {response})")
            return True

        except Exception as e:
            print(f"❌ [FCM] Ошибка отправки FCM: {e}")
            print(f"❌ [FCM] Тип ошибки: {type(e).__name__}")
            import traceback
            print(f"❌ [FCM] Stack trace: {traceback.format_exc()}")
            return False
    
    def send_photo_verification_approved(self, fcm_token: str, driver_name: str) -> bool:
        """
        Отправка уведомления об одобрении документов
        """
        print(f"🔍 [FCM] Отправляем уведомление об одобрении для водителя: {driver_name}")
        data = {
            'type': 'photo_verification_approved',
            'driver_name': driver_name
        }
        print(f"🔍 [FCM] Данные уведомления: {data}")
        return self.send_notification(
            fcm_token=fcm_token,
            title="Документы одобрены",
            body="Все документы проверены. Можете выходить на линию!",
            data=data
        )
    
    def send_photo_verification_rejected(
        self,
        fcm_token: str,
        driver_name: str,
        rejection_reason: str
    ) -> bool:
        """
        Отправка уведомления об отклонении документов
        """
        print(f"🔍 [FCM] Отправляем уведомление об отклонении для водителя: {driver_name}")
        print(f"🔍 [FCM] Причина отклонения: {rejection_reason}")
        data = {
            'type': 'photo_verification_rejected',
            'driver_name': driver_name,
            'rejection_reason': rejection_reason
        }
        print(f"🔍 [FCM] Данные уведомления: {data}")
        return self.send_notification(
            fcm_token=fcm_token,
            title="Документы отклонены",
            body="Документы требуют доработки. Зайдите в приложение для просмотра причин",
            data=data
        )

    def send_balance_topup(
        self,
        fcm_token: str,
        driver_name: str,
        amount: float,
        new_balance: float
    ) -> bool:
        """
        Отправка уведомления о пополнении баланса
        """
        print(f"🔍 [FCM] Отправляем уведомление о пополнении баланса для водителя: {driver_name}")
        print(f"🔍 [FCM] Сумма пополнения: {amount} сом")
        print(f"🔍 [FCM] Новый баланс: {new_balance} сом")
        data = {
            'type': 'balance_topup',
            'driver_name': driver_name,
            'amount': str(amount),
            'new_balance': str(new_balance)
        }
        print(f"🔍 [FCM] Данные уведомления: {data}")
        return self.send_notification(
            fcm_token=fcm_token,
            title="Баланс пополнен",
            body=f"Ваш баланс пополнен на {amount} сом. Текущий баланс: {new_balance} сом",
            data=data
        )

# Глобальный экземпляр сервиса
fcm_service = FCMService()
