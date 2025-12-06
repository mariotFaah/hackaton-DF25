#!/usr/bin/env python3
"""
Scraper optimisé pour asako.mg - Scraping direct vers MySQL
Objectif: Récupérer au moins 50 offres réelles pour le hackathon
"""

import urllib.request
import re
from datetime import datetime, timedelta
import time
import sys
import os

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database.models import JobOffer, SessionLocal
    print("✅ Modules MySQL chargés")
except ImportError as e:
    print(f"❌ Erreur import MySQL: {e}")
    print("⚠  Mode scraping seul activé")
    JobOffer = None
    SessionLocal = None

class AsakoScraper:
    def __init__(self, use_database=True):
        self.base_url = "https://www.asako.mg"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 SafeAI-Hackathon/1.0'
        }
        self.use_database = use_database and JobOffer is not None
        print(f"🤖 Scraper initialisé (MySQL: {self.use_database})")
    
    def fetch_page(self, url):
        """Récupérer une page HTML avec retry"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=20) as response:
                    if response.status == 200:
                        html_content = response.read().decode('utf-8', errors='ignore')
                        print(f"✅ Page chargée: {url}")
                        return html_content
                    else:
                        print(f"⚠  Statut {response.status} pour {url}")
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⏳ Tentative {attempt + 1}/{max_retries} échouée pour {url}: {e}")
                    time.sleep(2)
                else:
                    print(f"❌ Erreur pour {url} après {max_retries} tentatives: {e}")
        return None
    
    def extract_offers_html(self, html):
        """Extraire le HTML de chaque offre - version améliorée"""
        if not html:
            return []
        
        # Pattern amélioré pour détecter les offres
        patterns = [
            r'<div class="d-flex item">(.*?)</div>\s*</div>\s*</div>\s*</div>',
            r'<div class="[^"]*item[^"]*">(.*?)</div>\s*</div>\s*</div>',
            r'<div[^>]*class="[^"]*offer[^"]*"[^>]*>(.*?)</div>\s*</div>'
        ]
        
        for pattern in patterns:
            offers_html = re.findall(pattern, html, re.DOTALL)
            if offers_html:
                print(f"📊 {len(offers_html)} offres détectées avec pattern")
                return offers_html
        
        # Fallback: chercher par structure commune
        offers_sections = re.findall(r'<h3>\s*<a[^>]*>.*?</a>\s*</h3>.*?<span class="date-pub">.*?</span>', html, re.DOTALL)
        if offers_sections:
            print(f"📊 {len(offers_sections)} offres détectées (fallback)")
            return offers_sections
        
        print("⚠  Aucune offre détectée avec les patterns actuels")
        return []
    
    def parse_offer(self, html):
        """Parser une offre individuelle - version robuste"""
        try:
            # Titre - version plus robuste
            title = "Non spécifié"
            title_match = re.search(r'<h3[^>]*>\s*<a[^>]*>(.*?)</a>', html, re.DOTALL)
            if title_match:
                title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                if not title or len(title) < 2:
                    title_match2 = re.search(r'title="([^"]+)"', html)
                    if title_match2:
                        title = title_match2.group(1).strip()
            
            # Lien
            link = ""
            link_match = re.search(r'href="(/annonces/[^"]+)"', html)
            if link_match:
                link = self.base_url + link_match.group(1)
            else:
                # Fallback pour lien
                link_match = re.search(r'href="(/offre/[^"]+)"', html)
                if link_match:
                    link = self.base_url + link_match.group(1)
            
            # Entreprise
            company = "Non spécifié"
            company_match = re.search(r'/profil-entreprise/([^"/]+)', html)
            if company_match:
                company = company_match.group(1).replace('-', ' ').title()
            else:
                company_match = re.search(r'<span[^>]*class="[^"]*company[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
                if company_match:
                    company = re.sub(r'<[^>]+>', '', company_match.group(1)).strip()
            
            # Date
            date_str = "Aujourd'hui"
            date_match = re.search(r'<span[^>]*class="[^"]*date-pub[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
            if date_match:
                date_str = re.sub(r'<[^>]+>', '', date_match.group(1)).strip()
            
            # Type de contrat
            contrat = "Non spécifié"
            contrat_match = re.search(r'<span[^>]*class="[^"]*contrat-type[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
            if contrat_match:
                contrat = contrat_match.group(1).strip()
            
            # Secteur
            secteur = "Non spécifié"
            secteur_match = re.search(r'<a[^>]*href="/emploi/s-[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
            if secteur_match:
                secteur = secteur_match.group(1).strip()
            
            # Métier
            metier = "Non spécifié"
            metier_match = re.search(r'<a[^>]*href="/emploi/m-[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
            if metier_match:
                metier = metier_match.group(1).strip()
            
            # Localisation
            location = "Antananarivo"  # Par défaut
            location_match = re.search(r'<a[^>]*href="/emploi/v-[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
            if location_match:
                location = location_match.group(1).strip()
            
            # Calculer le risque IA
            ia_risk_score = self.calculate_ia_risk(title, metier, secteur, contrat)
            ia_risk_level = self.get_risk_level(ia_risk_score)
            
            # Suggestions de reconversion
            suggestions = self.get_reconversion_suggestions(metier, secteur, ia_risk_score)
            
            # Description (simplifiée)
            description = self.extract_description(html)
            
            return {
                'title': title[:200],
                'link': link[:500],
                'company': company[:100],
                'date': self.clean_date(date_str),
                'contrat': contrat[:50],
                'secteur': secteur[:100],
                'metier': metier[:100],
                'location': location[:100],
                'description': description[:500],
                'ia_risk_score': ia_risk_score,
                'ia_risk_level': ia_risk_level,
                'suggestions': suggestions,
                'scraped_at': datetime.now()
            }
            
        except Exception as e:
            print(f"⚠ Erreur parsing offre: {e}")
            return None
    
    def clean_date(self, date_str):
        """Nettoyer et formater la date"""
        if not date_str or date_str == "Non spécifié":
            return datetime.now().strftime("%Y-%m-%d")
        
        date_str = date_str.strip().lower()
        
        # Gérer les formats français
        if "aujourd'hui" in date_str or "today" in date_str:
            return datetime.now().strftime("%Y-%m-%d")
        elif "hier" in date_str or "yesterday" in date_str:
            return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        elif "il y a" in date_str:
            # Extraire le nombre de jours
            days_match = re.search(r'(\d+)', date_str)
            if days_match:
                days_ago = int(days_match.group(1))
                return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        return datetime.now().strftime("%Y-%m-%d")
    
    def extract_description(self, html):
        """Extraire la description simplifiée"""
        desc_match = re.search(r'<p[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</p>', html, re.DOTALL)
        if desc_match:
            description = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()
            return description[:200] + "..." if len(description) > 200 else description
        return "Description non disponible"
    
    def calculate_ia_risk(self, title, metier, secteur, contrat):
        """Calculer un score de risque d'automatisation par l'IA"""
        score = 5.0
        
        # Combiner tout le texte pour l'analyse
        text = f"{title} {metier} {secteur} {contrat}".lower()
        
        # Score basé sur le métier (priorité haute)
        metier_risks = {
            'chauffeur': 9.0, 'conducteur': 9.0, 'driver': 9.0,
            'livreur': 8.5, 'delivery': 8.5, 'coursier': 8.5,
            'caissier': 8.0, 'cashier': 8.0,
            'téléopérateur': 7.5, 'call center': 7.5, 'téléconseiller': 7.5,
            'secrétaire': 7.0, 'secretary': 7.0, 'assistant': 6.5,
            'opérateur': 7.0, 'operator': 7.0,
            'mécanicien': 6.0, 'mechanic': 6.0,
            'comptable': 5.0, 'accountant': 5.0,
            'enseignant': 2.0, 'teacher': 2.0, 'professeur': 2.0,
            'médecin': 1.5, 'doctor': 1.5,
            'infirmier': 2.0, 'nurse': 2.0,
            'développeur': 3.0, 'developer': 3.0,
            'manager': 2.5, 'directeur': 2.0, 'chef': 2.5,
            'coordinateur': 2.0, 'coordinator': 2.0,
            'conseiller': 3.0, 'consultant': 3.0,
        }
        
        for job, risk in metier_risks.items():
            if job in text:
                score = risk
                break  # Prendre le premier métier trouvé
        
        # Ajustements par secteur
        if any(word in text for word in ['transport', 'logistique', 'delivery']):
            score += 1.0
        if any(word in text for word in ['industrie', 'production', 'manufacturing']):
            score += 1.5
        if any(word in text for word in ['commerce', 'retail', 'supermarket']):
            score += 0.5
        if any(word in text for word in ['technologie', 'tech', 'it', 'informatique']):
            score -= 1.0
        if any(word in text for word in ['santé', 'health', 'medical']):
            score -= 1.5
        if any(word in text for word in ['éducation', 'education', 'formation']):
            score -= 1.0
        
        # Ajustements par mots-clés
        high_risk_words = ['répétitif', 'routine', 'standard', 'process', 'assembly']
        for word in high_risk_words:
            if word in text:
                score += 0.5
        
        low_risk_words = ['créatif', 'creative', 'design', 'gestion', 'management', 'relation client']
        for word in low_risk_words:
            if word in text:
                score -= 0.5
        
        # Garder dans les limites
        return round(max(1.0, min(10.0, score)), 1)
    
    def get_risk_level(self, score):
        """Convertir score en niveau de risque"""
        if score >= 8.0:
            return "Élevé"
        elif score >= 5.0:
            return "Moyen"
        else:
            return "Faible"
    
    def get_reconversion_suggestions(self, metier, secteur, score):
        """Générer des suggestions de reconversion"""
        suggestions = []
        
        if score >= 8.0:  # Risque élevé
            suggestions = [
                "Formation en compétences numériques (Excel, outils de gestion)",
                "Reconversion vers la logistique ou la coordination",
                "Développement de compétences en gestion de projet",
                "Apprentissage des outils de relation client (CRM)"
            ]
        elif score >= 5.0:  # Risque moyen
            suggestions = [
                "Renforcement des compétences relationnelles",
                "Apprentissage des outils digitaux de votre secteur",
                "Spécialisation dans un créneau à forte valeur ajoutée"
            ]
        else:  # Risque faible
            suggestions = [
                "Continuer à se former dans votre domaine",
                "Développer une expertise complémentaire",
                "Renforcer vos compétences en leadership"
            ]
        
        return suggestions
    
    def save_to_database(self, offer_data):
        """Sauvegarder une offre en base de données - version simplifiée"""
        if not self.use_database:
            return False
        
        try:
            db = SessionLocal()
            
            # Vérifier si l'offre existe déjà (juste par lien)
            existing = db.query(JobOffer.id).filter(
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
                    description=offer_data['description'],
                    ia_risk_score=offer_data['ia_risk_score'],
                    ia_risk_level=offer_data['ia_risk_level'],
                    suggestions=', '.join(offer_data['suggestions']),
                    scraped_at=datetime.now(),
                    is_active=True
                )
                db.add(job_offer)
                db.commit()
                db.close()
                return True
            else:
                db.close()
                return False  # Déjà existante
                
        except Exception as e:
            print(f"❌ Erreur base de données: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return False
    
    def scrape_category(self, category, pages=2):
        """Scraper une catégorie - version simplifiée"""
        print(f"\n{'='*60}")
        print(f"📥 SCRAPING: {category.upper()}")
        print(f"{'='*60}")
        
        all_offers = []
        saved_count = 0
        
        for page in range(1, pages + 1):
            if page == 1:
                url = f"{self.base_url}/{category}"
            else:
                url = f"{self.base_url}/{category}?page={page}"
            
            print(f"\n📄 Page {page}/{pages}: {url}")
            
            html = self.fetch_page(url)
            if not html:
                print("   ⏭️  Page vide ou erreur, on continue...")
                continue
            
            offers_html = self.extract_offers_html(html)
            
            if not offers_html:
                print("   ⚠  Aucune offre détectée sur cette page")
                continue
            
            page_saved = 0
            for i, offer_html in enumerate(offers_html, 1):
                offer_data = self.parse_offer(offer_html)
                if offer_data and offer_data['link']:
                    all_offers.append(offer_data)
                    
                    if self.use_database:
                        if self.save_to_database(offer_data):
                            page_saved += 1
                            saved_count += 1
            
            print(f"   ✅ {page_saved} nouvelles offres sauvegardées sur cette page")
            
            # Pause entre les pages pour être gentil
            if page < pages:
                time.sleep(1.5)
        
        # Afficher le résumé
        if all_offers:
            print(f"\n📊 RÉSULTAT {category.upper()}:")
            print(f"   • Offres analysées: {len(all_offers)}")
            print(f"   • Nouvelles offres sauvegardées: {saved_count}")
            
            # Statistiques de risque
            risk_counts = {"Élevé": 0, "Moyen": 0, "Faible": 0}
            for offer in all_offers:
                level = offer.get('ia_risk_level', 'Inconnu')
                if level in risk_counts:
                    risk_counts[level] += 1
            
            print(f"   • Risque élevé: {risk_counts['Élevé']}")
            print(f"   • Risque moyen: {risk_counts['Moyen']}")
            print(f"   • Risque faible: {risk_counts['Faible']}")
            
            # Exemple d'offre à haut risque
            high_risk = [o for o in all_offers if o.get('ia_risk_level') == 'Élevé']
            if high_risk:
                print(f"\n   🚨 EXEMPLE À HAUT RISQUE:")
                example = high_risk[0]
                print(f"      Titre: {example['title'][:50]}...")
                print(f"      Métier: {example['metier']}")
                print(f"      Score IA: {example['ia_risk_score']}/10")
        
        return all_offers
    
    def scrape_all_for_hackathon(self):
        """Scraper toutes les catégories pour le hackathon"""
        print("\n" + "="*60)
        print("🚀 LANCEMENT DU SCRAPING POUR LE HACKATHON")
        print("Objectif: Récupérer au moins 50 offres réelles")
        print("="*60)
        
        # Catégories et nombre de pages pour chacune
        categories_config = {
            "cdd": 3,      # CDD - souvent beaucoup d'offres
            "emploi": 5,   # Toutes les offres
            "freelance": 2, # Freelance
            "stage": 2,    # Stages
            "cdi": 2       # CDI
        }
        
        total_offers = []
        total_saved = 0
        
        for category, pages in categories_config.items():
            try:
                offers = self.scrape_category(category, pages=pages)
                if offers:
                    total_offers.extend(offers)
                    # Compter combien ont été sauvegardés
                    for offer in offers:
                        if offer.get('link'):
                            total_saved += 1
            except Exception as e:
                print(f"❌ Erreur avec {category}: {e}")
                continue
        
        # Résumé final
        print(f"\n{'='*60}")
        print("🎯 RÉSUMÉ FINAL DU SCRAPING")
        print(f"{'='*60}")
        print(f"📊 Total offres analysées: {len(total_offers)}")
        print(f"💾 Offres dans MySQL: {total_saved}")
        
        if total_offers:
            # Statistiques globales
            risk_counts = {"Élevé": 0, "Moyen": 0, "Faible": 0}
            metiers = {}
            
            for offer in total_offers:
                level = offer.get('ia_risk_level', 'Inconnu')
                if level in risk_counts:
                    risk_counts[level] += 1
                
                metier = offer.get('metier', 'Inconnu')
                metiers[metier] = metiers.get(metier, 0) + 1
            
            print(f"\n📈 DISTRIBUTION DES RISQUES:")
            for level, count in risk_counts.items():
                percentage = (count / len(total_offers) * 100) if total_offers else 0
                print(f"   • {level}: {count} offres ({percentage:.1f}%)")
            
            print(f"\n🏆 TOP 5 MÉTIERS:")
            top_metiers = sorted(metiers.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (metier, count) in enumerate(top_metiers, 1):
                print(f"   {i}. {metier}: {count} offres")
            
            # Suggestions pour la démo
            high_risk_offers = [o for o in total_offers if o.get('ia_risk_level') == 'Élevé']
            if high_risk_offers:
                print(f"\n💡 POUR LA DÉMO DU HACKATHON:")
                print(f"   Vous avez {len(high_risk_offers)} offres à haut risque!")
                print(f"   Exemples parfaits pour montrer l'impact de l'IA")
        
        return total_offers

def main():
    """Fonction principale simplifiée"""
    print("\n" + "="*60)
    print("🤖 SCRAPER SAFE AI HACKATHON - VERSION OPTIMISÉE")
    print("Scraping automatique vers MySQL")
    print("="*60)
    
    # Mode automatique - toujours avec MySQL
    use_mysql = True
    
    scraper = AsakoScraper(use_database=use_mysql)
    
    # Lancer le scraping complet
    offers = scraper.scrape_all_for_hackathon()
    
    # Messages finaux
    if offers:
        print(f"\n✅ SCRAPING TERMINÉ AVEC SUCCÈS!")
        print(f"   → {len(offers)} offres analysées")
        print(f"   → Données disponibles dans MySQL")
        print(f"\n🎯 PROCHAINES ÉTAPES:")
        print("1. Démarrer l'API: python3 run.py")
        print("2. Tester: curl http://localhost:5000/api/health")
        print("3. Vérifier: curl http://localhost:5000/api/offers")
    else:
        print(f"\n⚠  ATTENTION: Peu ou pas de données récupérées")
        print("   Vérifiez votre connexion internet")
        print("   Le site asako.mg peut être temporairement indisponible")

if __name__ == "__main__":
    main()