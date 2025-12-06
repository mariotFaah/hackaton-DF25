"""
Scraper qui sauvegarde dans MySQL
"""

from sqlalchemy.orm import Session
from database.models import JobOffer, SessionLocal, get_db
from datetime import datetime
import re

class MySQLScraper:
    def __init__(self):
        self.base_url = "https://www.asako.mg"
        self.headers = {'User-Agent': 'SafeAI-Hackathon/1.0'}
    
    def scrape_and_save(self, category):
        """Scraper une catégorie et sauvegarder en base"""
        print(f"🚀 Scraping {category} vers MySQL...")
        
        # Scraper le HTML (même code qu'avant)
        html = self.fetch_page(f"{self.base_url}/{category}")
        if not html:
            return []
        
        offers_html = self.extract_offers_html(html)
        
        # Sauvegarder en base
        db = SessionLocal()
        saved_count = 0
        
        for offer_html in offers_html:
            offer_data = self.parse_offer(offer_html)
            if offer_data:
                # Vérifier si l'offre existe déjà
                existing = db.query(JobOffer).filter(
                    JobOffer.link == offer_data['link']
                ).first()
                
                if not existing:
                    # Créer une nouvelle offre
                    job_offer = JobOffer(
                        title=offer_data['title'],
                        link=offer_data['link'],
                        company=offer_data['company'],
                        date_posted=offer_data['date'],
                        contract_type=offer_data['contrat'],
                        sector=offer_data['secteur'],
                        job_title=offer_data['metier'],
                        location=offer_data['location'],
                        ia_risk_score=offer_data['ia_risk_score'],
                        ia_risk_level=offer_data['ia_risk_level'],
                        scraped_at=datetime.utcnow()
                    )
                    db.add(job_offer)
                    saved_count += 1
                else:
                    # Mettre à jour l'offre existante
                    existing.ia_risk_score = offer_data['ia_risk_score']
                    existing.ia_risk_level = offer_data['ia_risk_level']
                    existing.scraped_at = datetime.utcnow()
        
        db.commit()
        db.close()
        
        print(f"✅ {saved_count} nouvelles offres sauvegardées")
        return saved_count
    
    # ... (les méthodes fetch_page, extract_offers_html, parse_offer restent les mêmes)