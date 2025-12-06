"""
Configuration de l'application
"""

import os
from pathlib import Path

# Chemins
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SCRAPERS_DIR = BASE_DIR / "scrapers"

# Fichiers de données
OFFERS_FILE = DATA_DIR / "offres_toutes.json"
CATEGORY_FILES = {
    "cdd": DATA_DIR / "offres_cdd.json",
    "cdi": DATA_DIR / "offres_cdi.json",
    "emploi": DATA_DIR / "offres_emploi.json",
}

# Configuration API
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": True,
    "cors_origins": ["http://localhost:3000"],  # React par défaut
}

# Configuration scraping
SCRAPING_CONFIG = {
    "base_url": "https://www.asako.mg",
    "user_agent": "SafeAI-Hackathon/1.0",
    "timeout": 10,
    "categories": ["cdd", "cdi", "emploi", "stage", "freelance"],
}