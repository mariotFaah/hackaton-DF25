"""
Configuration de l'application
"""

import os
from datetime import timedelta

class Config:
    """Configuration de base"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'safe-ai-hackathon-secret-key')
    DEBUG = os.getenv('FLASK_DEBUG', True)
    
    # Base de données - AVEC LE BON MOT DE PASSE
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://admin:mot_de_passe@localhost/safe_ai_hackathon')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CORS
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"]
    
    # API
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 5000))
    
    # Scraping
    SCRAPE_INTERVAL_HOURS = 6
    MAX_OFFERS_PER_CATEGORY = 100
    
    # Analyse IA
    HIGH_RISK_THRESHOLD = 7.5
    MEDIUM_RISK_THRESHOLD = 5.0
    
    # Fichiers
    DATA_DIR = "data"
    LOG_DIR = "logs"

# Configuration pour l'API (compatibilité)
API_CONFIG = {
    "host": Config.API_HOST,
    "port": Config.API_PORT,
    "debug": Config.DEBUG,
    "cors_origins": Config.CORS_ORIGINS
}

# Pour compatibilité
app_config = Config

# AJOUTEZ CETTE LIGNE POUR LA COMPATIBILITÉ
DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI
