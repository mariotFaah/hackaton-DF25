"""
Modèles de base de données SQLAlchemy
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, text
from datetime import datetime
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

Base = declarative_base()

class JobOffer(Base):
    __tablename__ = 'job_offers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    link = Column(String(500), unique=True, nullable=False)
    company = Column(String(200))
    date_posted = Column(String(100))
    contract_type = Column(String(100))
    sector = Column(String(200))
    job_title = Column(String(200))
    location = Column(String(200))
    description = Column(Text, default='')
    ia_risk_score = Column(Float)
    ia_risk_level = Column(String(50))
    suggestions = Column(Text)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class JobRecommendation(Base):
    __tablename__ = 'job_recommendations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    original_job_id = Column(Integer, ForeignKey('job_offers.id', ondelete='CASCADE'))
    recommended_job_id = Column(Integer, ForeignKey('job_offers.id', ondelete='CASCADE'))
    score_difference = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    original_job = relationship("JobOffer", foreign_keys=[original_job_id])
    recommended_job = relationship("JobOffer", foreign_keys=[recommended_job_id])

class Statistics(Base):
    __tablename__ = 'statistics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey('job_offers.id', ondelete='CASCADE'))
    analysis_type = Column(String(100))
    data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relation
    job = relationship("JobOffer")

# Configuration de la base de données
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://admin:mot_de_passe@localhost/safe_ai_hackathon')

print(f"🔗 Tentative de connexion à: {DATABASE_URL.replace(':mot_de_passe', ':******')}")

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("✅ Connexion à MySQL réussie!")
except Exception as e:
    print(f"❌ Erreur de connexion à MySQL: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialiser la base de données - NE PAS UTILISER car tables existent déjà"""
    print("ℹ️  Les tables existent déjà (créées par repair_database.py)")
    print("ℹ️  Pour recréer, exécutez: python3 repair_database.py")
    return True

def get_db():
    """Obtenir une session de base de données"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Méthode pour convertir en dictionnaire
def to_dict(self):
    """Convertir l'objet en dictionnaire"""
    return {
        'id': self.id,
        'title': self.title,
        'link': self.link,
        'company': self.company,
        'date': self.date_posted,
        'contrat': self.contract_type,
        'secteur': self.sector,
        'metier': self.job_title,
        'location': self.location,
        'description': self.description,
        'ia_risk_score': float(self.ia_risk_score) if self.ia_risk_score else 0.0,
        'ia_risk_level': self.ia_risk_level,
        'suggestions': self.suggestions.split(', ') if self.suggestions else [],
        'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
        'is_active': self.is_active
    }

# Attacher la méthode à la classe
JobOffer.to_dict = to_dict