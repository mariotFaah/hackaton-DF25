"""
Modèle de données pour les offres d'emploi
"""

from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class JobOffer:
    """Représente une offre d'emploi"""
    title: str
    link: str
    company: str
    date: str
    contrat: str
    secteur: str
    metier: str
    location: str
    ia_risk_score: int
    ia_risk_level: str
    
    def to_dict(self):
        """Convertir en dictionnaire pour JSON"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        """Créer à partir d'un dictionnaire"""
        return cls(**data)
    
    @property
    def is_high_risk(self) -> bool:
        """Vérifier si risque élevé"""
        return self.ia_risk_level == "Élevé"
    
    @property
    def is_low_risk(self) -> bool:
        """Vérifier si risque faible"""
        return self.ia_risk_level == "Faible"

class JobOfferCollection:
    """Collection d'offres d'emploi avec méthodes utilitaires"""
    
    def __init__(self, offers=None):
        self.offers = offers or []
    
    def add_offer(self, offer: JobOffer):
        """Ajouter une offre"""
        self.offers.append(offer)
    
    def filter_by_job(self, job_name: str) -> 'JobOfferCollection':
        """Filtrer par nom de métier"""
        filtered = [
            offer for offer in self.offers 
            if job_name.lower() in offer.metier.lower()
        ]
        return JobOfferCollection(filtered)
    
    def filter_by_risk(self, risk_level: str) -> 'JobOfferCollection':
        """Filtrer par niveau de risque"""
        filtered = [
            offer for offer in self.offers 
            if offer.ia_risk_level == risk_level
        ]
        return JobOfferCollection(filtered)
    
    def filter_by_sector(self, sector: str) -> 'JobOfferCollection':
        """Filtrer par secteur"""
        filtered = [
            offer for offer in self.offers 
            if sector.lower() in offer.secteur.lower()
        ]
        return JobOfferCollection(filtered)
    
    def get_statistics(self) -> dict:
        """Obtenir des statistiques"""
        if not self.offers:
            return {}
        
        total = len(self.offers)
        high_risk = len([o for o in self.offers if o.is_high_risk])
        low_risk = len([o for o in self.offers if o.is_low_risk])
        avg_score = sum(o.ia_risk_score for o in self.offers) / total
        
        # Métiers les plus courants
        jobs = {}
        for offer in self.offers:
            jobs[offer.metier] = jobs.get(offer.metier, 0) + 1
        
        top_jobs = sorted(jobs.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_offers": total,
            "high_risk_count": high_risk,
            "low_risk_count": low_risk,
            "average_risk_score": round(avg_score, 2),
            "top_jobs": dict(top_jobs)
        }