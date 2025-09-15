from app.database.session import engine, SessionLocal
from app.models.superadmin import SuperAdmin
from app.models.driver import Driver
from app.models.order import Order
from app.models.taxipark import TaxiPark
from app.models.administrator import Administrator
from app.models.transaction import DriverTransaction
from app.core.security import get_password_hash

def init_database():
    # Создаем все таблицы
    SuperAdmin.__table__.create(bind=engine, checkfirst=True)
    Driver.__table__.create(bind=engine, checkfirst=True)
    Order.__table__.create(bind=engine, checkfirst=True)
    TaxiPark.__table__.create(bind=engine, checkfirst=True)
    Administrator.__table__.create(bind=engine, checkfirst=True)
    DriverTransaction.__table__.create(bind=engine, checkfirst=True)

    db = SessionLocal()

    try:
        # Создаем только первого суперадмина
        existing_admin = db.query(SuperAdmin).filter(SuperAdmin.login == "Alexander").first()

        if not existing_admin:
            hashed_password = get_password_hash("123")
            first_admin = SuperAdmin(
                login="Alexander",
                hashed_password=hashed_password,
                position="Главный разработчик"
            )
            db.add(first_admin)
            db.commit()
            print("✅ Первый суперадмин 'Alexander' создан!")
        else:
            print("✅ Суперадмин 'Alexander' уже существует!")

        print("✅ База данных инициализирована успешно!")
        print("📊 Созданы таблицы: superadmins, drivers, orders, taxiparks, administrators, transactions")

    except Exception as e:
        print(f"❌ Ошибка при инициализации БД: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
