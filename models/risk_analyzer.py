"""
Algorithme d'analyse de risque IA
"""

import re
from typing import List, Dict

class RiskAnalyzer:
    """Analyse le risque d'automatisation par l'IA"""
    
    def __init__(self):
        # Dictionnaire de risques par mot-clé
        self.risk_keywords = {
            "high_risk": [
                ("conducteur", 3), ("chauffeur", 3), ("driver", 3),
                ("saisie", 4), ("data entry", 4), ("traitement données", 3),
                ("téléopérateur", 3), ("call center", 3), ("standardiste", 2),
                ("réceptionniste", 2), ("agent", 2), ("opérateur", 2),
                ("production", 2), ("assemblage", 2), ("routine", 2),
            ],
            "medium_risk": [
                ("comptable", 1), ("comptabilité", 1),
                ("assistant", 1), ("secrétaire", 1),
                ("commercial", 1), ("vente", 1),
                ("technicien", 1), ("maintenance", 1),
            ],
            "protection": [  # Diminue le risque
                ("manager", -3), ("directeur", -3), ("chef", -2),
                ("superviseur", -2), ("coordinateur", -2),
                ("créatif", -2), ("design", -2), ("conception", -2),
                ("innovation", -2), ("stratège", -3),
                ("analyste", -1), ("consultant", -1),
                ("relation client", -2), ("négociation", -2),
                ("gestion", -1), ("leadership", -3), ("formation", -1),
                ("développeur", -1), ("ingénieur", -1),
            ]
        }
    
    def calculate_risk_score(self, title: str, metier: str, secteur: str) -> int:
        """Calculer un score de risque (1-10)"""
        score = 5  # Neutre
        text = f"{title} {metier} {secteur}".lower()
        
        # Appliquer les points de risque
        for category, keywords in self.risk_keywords.items():
            for keyword, points in keywords:
                if keyword in text:
                    score += points
        
        # Cas spéciaux
        if 'mécanicien' in text and 'conducteur' in text:
            score += 2  # Double compétence
        
        # Normaliser entre 1 et 10
        return max(1, min(10, score))
    
    def get_risk_level(self, score: int) -> str:
        """Convertir score en niveau de risque"""
        if score >= 8:
            return "Élevé"
        elif score >= 5:
            return "Moyen"
        else:
            return "Faible"
    
    def analyze_job_transition(self, current_job: str, all_offers: List[Dict]) -> List[Dict]:
        """
        Trouver des alternatives à moindre risque pour un métier donné
        
        Args:
            current_job: Métier actuel
            all_offers: Liste de toutes les offres
        
        Returns:
            Liste des recommandations triées par différence de risque
        """
        # Trouver les offres pour le métier actuel
        current_offers = [
            o for o in all_offers 
            if current_job.lower() in o.get('metier', '').lower()
        ]
        
        if not current_offers:
            return []
        
        # Calculer le risque moyen du métier actuel
        current_avg_risk = sum(o.get('ia_risk_score', 5) for o in current_offers) / len(current_offers)
        
        # Trouver des alternatives dans le même secteur
        current_sectors = set(o.get('secteur') for o in current_offers)
        recommendations = []
        
        for offer in all_offers:
            # Éviter le même métier
            if current_job.lower() in offer.get('metier', '').lower():
                continue
            
            # Vérifier si c'est dans un secteur similaire
            if offer.get('secteur') in current_sectors:
                risk_diff = current_avg_risk - offer.get('ia_risk_score', 5)
                
                if risk_diff > 0:  # Seulement si moins risqué
                    recommendations.append({
                        **offer,
                        'difference_risk': round(risk_diff, 1)
                    })
        
        # Trier par différence de risque (plus grande différence en premier)
        recommendations.sort(key=lambda x: x['difference_risk'], reverse=True)
        
        return recommendations[:10]  # Limiter à 10 recommandations