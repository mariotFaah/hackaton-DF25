"""
Traitement des données scrapées
"""

import json
from pathlib import Path
from typing import List, Dict
from models.job_offer import JobOffer, JobOfferCollection
from models.risk_analyzer import RiskAnalyzer

class DataProcessor:
    """Gère le chargement et le traitement des données"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.risk_analyzer = RiskAnalyzer()
    
    def load_offers(self, filename: str = "offres_toutes.json") -> JobOfferCollection:
        """Charger les offres depuis un fichier JSON"""
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            return JobOfferCollection()
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        offers = []
        for item in data:
            try:
                offer = JobOffer(
                    title=item.get('title', ''),
                    link=item.get('link', ''),
                    company=item.get('company', ''),
                    date=item.get('date', ''),
                    contrat=item.get('contrat', ''),
                    secteur=item.get('secteur', ''),
                    metier=item.get('metier', 'Non spécifié'),
                    location=item.get('location', ''),
                    ia_risk_score=item.get('ia_risk_score', 5),
                    ia_risk_level=item.get('ia_risk_level', 'Moyen')
                )
                offers.append(offer)
            except Exception as e:
                print(f"Erreur chargement offre: {e}")
                continue
        
        return JobOfferCollection(offers)
    
    def save_offers(self, offers: JobOfferCollection, filename: str):
        """Sauvegarder les offres dans un fichier JSON"""
        filepath = self.data_dir / filename
        
        data = [offer.to_dict() for offer in offers.offers]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_risk_analysis(self, offers: JobOfferCollection) -> Dict:
        """Obtenir une analyse agrégée des risques"""
        stats = offers.get_statistics()
        
        # Analyse détaillée par métier
        job_analysis = {}
        jobs = {}
        
        for offer in offers.offers:
            metier = offer.metier
            if metier not in jobs:
                jobs[metier] = {
                    "count": 0,
                    "total_score": 0,
                    "high_risk": 0,
                    "medium_risk": 0,
                    "low_risk": 0
                }
            
            jobs[metier]["count"] += 1
            jobs[metier]["total_score"] += offer.ia_risk_score
            
            if offer.ia_risk_level == "Élevé":
                jobs[metier]["high_risk"] += 1
            elif offer.ia_risk_level == "Moyen":
                jobs[metier]["medium_risk"] += 1
            else:
                jobs[metier]["low_risk"] += 1
        
        # Calculer les moyennes
        for metier, data in jobs.items():
            if data["count"] > 0:
                data["average_score"] = round(data["total_score"] / data["count"], 2)
            else:
                data["average_score"] = 0
        
        return {
            "overall_statistics": stats,
            "job_analysis": jobs
        }