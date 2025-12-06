#!/usr/bin/env python3
"""
Scraper pour asako.mg - Hackathon Safe AI
Objectif: Analyser les offres pour évaluer le risque d'automatisation par l'IA
"""

import urllib.request
import re
import json
from datetime import datetime

class AsakoScraper:
    def __init__(self):
        self.base_url = "https://www.asako.mg"
        self.headers = {
            'User-Agent': 'SafeAI-Hackathon/1.0 (Analyse risque IA pour emplois)'
        }
    
    def fetch_page(self, url):
        """Récupérer une page HTML"""
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"❌ Erreur pour {url}: {e}")
            return None
    
    def extract_offers(self, html):
        """Extraire toutes les offres d'une page"""
        print("🔍 Extraction des offres...")
        
        # Pattern pour chaque offre
        offer_pattern = r'<div class="d-flex item">(.*?)</div>\s*</div>'
        offers_html = re.findall(offer_pattern, html, re.DOTALL)
        
        print(f"📊 Offres trouvées: {len(offers_html)}")
        
        offers = []
        
        for offer_html in offers_html:
            offer = self.parse_offer(offer_html)
            if offer:
                offers.append(offer)
        
        return offers
    
    def parse_offer(self, html):
        """Parser une offre individuelle"""
        try:
            # Titre
            title_match = re.search(r'<h3>\s*<a[^>]*>(.*?)</a>', html, re.DOTALL)
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else "Non spécifié"
            
            # Lien
            link_match = re.search(r'href="(/annonces/[^"]+)"', html)
            link = self.base_url + link_match.group(1) if link_match else ""
            
            # Entreprise
            company_match = re.search(r'/profil-entreprise/([^"]+)"', html)
            company = company_match.group(1) if company_match else "Non spécifié"
            
            # Date
            date_match = re.search(r'<span class="date-pub">(.*?)</span>', html)
            date = date_match.group(1).strip() if date_match else "Non spécifié"
            
            # Type de contrat
            contrat_match = re.search(r'<span>([^<]+)</span>', html)
            contrat = contrat_match.group(1) if contrat_match else "Non spécifié"
            
            # Secteur
            secteur_match = re.search(r'<a href="/emploi/s-[^"]*">([^<]+)</a>', html)
            secteur = secteur_match.group(1) if secteur_match else "Non spécifié"
            
            # Métier
            metier_match = re.search(r'<a href="/emploi/m-[^"]*">([^<]+)</a>', html)
            metier = metier_match.group(1) if metier_match else "Non spécifié"
            
            # Localisation
            location_match = re.search(r'<a href="/emploi/v-[^"]*">([^<]+)</a>', html)
            location = location_match.group(1) if location_match else "Non spécifié"
            
            # Calculer le risque IA
            ia_risk_score = self.calculate_ia_risk(title, metier, secteur)
            
            return {
                'title': title,
                'link': link,
                'company': company,
                'date': date,
                'contrat': contrat,
                'secteur': secteur,
                'metier': metier,
                'location': location,
                'ia_risk_score': ia_risk_score,
                'ia_risk_level': self.get_risk_level(ia_risk_score)
            }
            
        except Exception as e:
            print(f"⚠ Erreur parsing offre: {e}")
            return None
    
    def calculate_ia_risk(self, title, metier, secteur):
        """Calculer un score de risque d'automatisation par l'IA"""
        score = 5  # Score neutre de base
        
        text = f"{title} {metier} {secteur}".lower()
        
        # Facteurs qui augmentent le risque (tâches répétitives, manuelles)
        high_risk_keywords = [
            'saisie', 'data entry', 'répétitif', 'routine', 'standard',
            'process', 'assembly', 'production', 'manufacturing', 'operator',
            'cashier', 'teller', 'receptionist', 'clerk'
        ]
        
        for keyword in high_risk_keywords:
            if keyword in text:
                score += 2
        
        # Facteurs qui diminuent le risque (créativité, relationnel, management)
        low_risk_keywords = [
            'manager', 'directeur', 'chef', 'supervisor', 'coordinateur',
            'creative', 'créatif', 'design', 'conception', 'strateg',
            'analyst', 'analyste', 'consultant', 'relation client',
            'négociation', 'gestion', 'leadership', 'innovation'
        ]
        
        for keyword in low_risk_keywords:
            if keyword in text:
                score -= 2
        
        # Ajustements spécifiques par métier
        if 'chauffeur' in text or 'conducteur' in text or 'driver' in text:
            # Chauffeur: risque moyen-élevé avec voitures autonomes
            score += 3
        
        if 'mécanicien' in text or 'mechanic' in text:
            # Mécanicien: risque moyen (IA peut aider mais pas remplacer)
            score += 1
        
        # Garder le score entre 1 et 10
        return max(1, min(10, score))
    
    def get_risk_level(self, score):
        """Convertir score en niveau de risque"""
        if score >= 8:
            return "Élevé"
        elif score >= 5:
            return "Moyen"
        else:
            return "Faible"
    
    def scrape_category(self, category):
        """Scraper une catégorie spécifique"""
        print(f"\n🚀 Scraping catégorie: {category}")
        print("=" * 50)
        
        url = f"{self.base_url}/{category}"
        html = self.fetch_page(url)
        
        if not html:
            return []
        
        offers = self.extract_offers(html)
        
        # Analyser les résultats
        if offers:
            print(f"\n📈 Analyse des {len(offers)} offres:")
            
            # Compter par niveau de risque
            risk_counts = {"Élevé": 0, "Moyen": 0, "Faible": 0}
            for offer in offers:
                risk_counts[offer['ia_risk_level']] += 1
            
            print(f"  🔴 Risque élevé: {risk_counts['Élevé']} offres")
            print(f"  🟡 Risque moyen: {risk_counts['Moyen']} offres")
            print(f"  🟢 Risque faible: {risk_counts['Faible']} offres")
            
            # Afficher quelques offres à haut risque
            high_risk_offers = [o for o in offers if o['ia_risk_level'] == "Élevé"]
            if high_risk_offers:
                print(f"\n⚠  Offres à haut risque d'automatisation:")
                for offer in high_risk_offers[:3]:
                    print(f"  • {offer['title']} - {offer['metier']}")
                    print(f"    Score IA: {offer['ia_risk_score']}/10")
        
        return offers
    
    def save_to_json(self, offers, filename):
        """Sauvegarder les offres en JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(offers, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Données sauvegardées: {filename}")

def main():
    print("\n" + "="*60)
    print("🤖 SAFE AI HACKATHON - ANALYSE RISQUE IA")
    print("Scraping asako.mg pour évaluer le déplacement d'emplois")
    print("="*60)
    
    scraper = AsakoScraper()
    
    # Catégories à analyser (focus sur métiers manuels)
    categories = [
        "cdd",      # Contrats à durée déterminée
        "cdi",      # Contrats à durée indéterminée
        "emploi",   # Toutes les offres
    ]
    
    all_offers = []
    
    for category in categories:
        offers = scraper.scrape_category(category)
        all_offers.extend(offers)
        
        # Sauvegarder par catégorie
        scraper.save_to_json(offers, f"offres_{category}.json")
        
        print("\n" + "="*50)
    
    # Sauvegarder toutes les offres
    if all_offers:
        scraper.save_to_json(all_offers, "offres_toutes.json")
        
        print("\n🎯 RÉSUMÉ FINAL:")
        print(f"Total offres analysées: {len(all_offers)}")
        
        # Statistiques
        metiers = {}
        for offer in all_offers:
            metier = offer['metier']
            metiers[metier] = metiers.get(metier, 0) + 1
        
        print("\n📊 Top 5 métiers trouvés:")
        for metier, count in sorted(metiers.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  • {metier}: {count} offres")
        
        print("\n💡 Pour votre application React:")
        print("1. Utilisez ces données JSON comme base")
        print("2. Créez un algorithme de scoring IA plus sophistiqué")
        print("3. Proposez des alternatives aux métiers à haut risque")
        print("4. Ajoutez des formations pour se reconvertir")

if __name__ == "__main__":
    main()
