#!/usr/bin/env python3
"""
Correction du problème de sessions SQLAlchemy
"""

import sys
sys.path.append('.')

from database.db_manager import SessionLocal
from sqlalchemy import text

def test_session():
    """Test de session avec gestion propre"""
    db = None
    try:
        db = SessionLocal()
        # Test simple
        result = db.execute(text("SELECT 1")).scalar()
        print(f"✅ Session test: {result}")
        return True
    except Exception as e:
        print(f"❌ Session error: {e}")
        return False
    finally:
        if db:
            db.close()

def get_db_safe():
    """Version sécurisée de get_db"""
    db = SessionLocal()
    return db

if __name__ == "__main__":
    print("Testing database sessions...")
    for i in range(10):
        print(f"Test {i+1}: ", end="")
        test_session()
