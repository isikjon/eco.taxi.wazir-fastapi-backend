import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.session import engine

def upgrade():
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE drivers 
            ADD COLUMN online_status VARCHAR(20) DEFAULT 'offline' NOT NULL
        """))
        
        conn.execute(text("""
            ALTER TABLE drivers 
            ADD COLUMN last_online_at TIMESTAMP WITH TIME ZONE
        """))
        
        conn.commit()
        print("✅ Добавлены поля online_status и last_online_at в таблицу drivers")

def downgrade():
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE drivers DROP COLUMN IF EXISTS online_status"))
        conn.execute(text("ALTER TABLE drivers DROP COLUMN IF EXISTS last_online_at"))
        conn.commit()
        print("❌ Удалены поля online_status и last_online_at из таблицы drivers")

if __name__ == "__main__":
    upgrade()
