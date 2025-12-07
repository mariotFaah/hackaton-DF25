from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import config
import traceback

# Utilisez DATABASE_URL qui a été ajouté à config.py
DATABASE_URL = config.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10,
    echo=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

SessionScoped = scoped_session(SessionLocal)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    return SessionLocal()

def test_connection():
    db = None
    try:
        db = get_db_session()
        result = db.execute(text("SELECT 1")).scalar()
        print(f"✅ Connexion MySQL OK: {result}")
        return True
    except Exception as e:
        print(f"❌ Erreur connexion MySQL: {e}")
        return False
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    test_connection()
