#!/usr/bin/env python3
"""
Scheduler pour mettre à jour les données automatiquement
VERSION CORRIGÉE
"""

from apscheduler.schedulers.background import BackgroundScheduler
import time
import logging
import sys
import os
from datetime import datetime
from sqlalchemy import func  # ← IMPORT AJOUTÉ

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_job_data():
    """Tâche planifiée pour mettre à jour les données"""
    logger.info("="*60)
    logger.info(f"🔄 DÉBUT MISE À JOUR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    try:
        # Importer dynamiquement (éviter les problèmes de circular import)
        from scrapers.asako_scraper import AsakoScraper
        
        scraper = AsakoScraper(use_database=True)
        
        # Catégories à scraper (avec moins de pages pour une mise à jour rapide)
        categories_config = {
            "cdd": 1,      # 1 page seulement pour CDD
            "emploi": 2,   # 2 pages pour emploi général
        }
        
        total_analyzed = 0
        
        for category, pages in categories_config.items():
            try:
                logger.info(f"📥 Scraping: {category} ({pages} pages)")
                
                # Essayer différentes méthodes selon ce qui existe
                if hasattr(scraper, 'scrape_category'):
                    offers = scraper.scrape_category(category, pages=pages)
                elif hasattr(scraper, 'scrape_all_for_hackathon'):
                    # Si seule la méthode complète existe, on l'utilise pour toutes les catégories
                    offers = scraper.scrape_all_for_hackathon()
                    break  # Sortir après une exécution complète
                else:
                    logger.error(f"❌ Aucune méthode de scraping trouvée")
                    continue
                        
            except Exception as e:
                logger.error(f"❌ Erreur avec {category}: {e}")
                continue
            
            # Pause entre les catégories
            if category != list(categories_config.keys())[-1]:
                time.sleep(3)  # 3 secondes de pause
        
        # Log final - IMPORT CORRIGÉ
        try:
            from database.models import SessionLocal, JobOffer
            db = SessionLocal()
            try:
                total_in_db = db.query(func.count(JobOffer.id)).scalar() or 0
                logger.info(f"📊 Total offres en base: {total_in_db}")
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"⚠️  Impossible de compter les offres: {e}")
        
        logger.info(f"✅ MISE À JOUR TERMINÉE - {total_analyzed} offres analysées")
        logger.info("="*60)
        
        # Mettre à jour les stats API si l'API tourne
        update_api_stats()
        
    except Exception as e:
        logger.error(f"❌ ERREUR CRITIQUE dans update_job_data: {e}")
        import traceback
        logger.error(traceback.format_exc())

def update_api_stats():
    """Mettre à jour les stats de l'API si elle tourne"""
    try:
        import requests
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"🌐 API Status: {data.get('offers_count', 'N/A')} offres")
    except:
        logger.debug("API non accessible (normal si non démarrée)")

def start_scheduler(test_mode=False):
    """Démarrer le scheduler"""
    logger.info("🚀 INITIALISATION DU SCHEDULER")
    
    scheduler = BackgroundScheduler()
    
    if test_mode:
        # Mode test - exécution toutes les 10 minutes
        logger.info("🧪 MODE TEST ACTIVÉ - Exécution toutes les 10 minutes")
        scheduler.add_job(
            update_job_data,
            'interval',
            minutes=10,
            id='test_update',
            name='Mise à jour test'
        )
    else:
        # Mode production
        # 1. Toutes les 3 heures
        scheduler.add_job(
            update_job_data,
            'interval',
            hours=3,
            id='regular_update',
            name='Mise à jour régulière'
        )
        
        # 2. Tous les jours à minuit
        scheduler.add_job(
            update_job_data,
            'cron',
            hour=0,
            minute=0,
            id='daily_update',
            name='Mise à jour quotidienne'
        )
        
        # 3. Tous les jours à 6h, 12h, 18h
        for hour in [6, 12, 18]:
            scheduler.add_job(
                update_job_data,
                'cron',
                hour=hour,
                minute=0,
                id=f'update_{hour}h',
                name=f'Mise à jour {hour}h'
            )
    
    # Exécuter immédiatement une première fois
    scheduler.add_job(
        update_job_data,
        'date',
        run_date=datetime.now(),
        id='initial_update',
        name='Mise à jour initiale'
    )
    
    scheduler.start()
    logger.info("✅ SCHEDULER DÉMARRÉ")
    
    if test_mode:
        logger.info("⏳ Scheduler test en cours (Ctrl+C pour arrêter)")
    else:
        logger.info("⏳ Scheduler production en cours (Ctrl+C pour arrêter)")
    
    # Garder le script en cours d'exécution
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Arrêt du scheduler demandé...")
        scheduler.shutdown(wait=False)
        logger.info("👋 Scheduler arrêté")

def run_once():
    """Exécuter une seule fois (pour tests)"""
    logger.info("▶  EXÉCUTION UNIQUE DU SCRAPER")
    update_job_data()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("⏰ SCHEDULER SAFE AI - MISE À JOUR AUTOMATIQUE")
    print("="*60)
    
    # Vérifier les imports nécessaires
    try:
        from database.models import JobOffer
        logger.info("✅ Imports vérifiés")
    except ImportError as e:
        logger.error(f"❌ Import manquant: {e}")
        sys.exit(1)
    
    # Menu simple
    print("\n🎯 OPTIONS:")
    print("1. Mode test (toutes les 10 min)")
    print("2. Mode production (planification normale)")
    print("3. Exécuter une seule fois")
    print("4. Quitter")
    
    choice = input("\nVotre choix (1-4): ").strip()
    
    if choice == '1':
        start_scheduler(test_mode=True)
    elif choice == '2':
        start_scheduler(test_mode=False)
    elif choice == '3':
        run_once()
    elif choice == '4':
        print("👋 Au revoir!")
        sys.exit(0)
    else:
        print("❌ Choix invalide, utilisation du mode test par défaut")
        start_scheduler(test_mode=True)