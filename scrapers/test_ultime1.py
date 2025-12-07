#!/usr/bin/env python3
"""
PortalJob Madagascar Scraper - Version intégrée avec système source
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import time
import sys
import os

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database.models import JobOffer, SessionLocal
    print("✅ Modules MySQL chargés pour PortalJob")
except ImportError as e:
    print(f"❌ Erreur import MySQL: {e}")
    print("⚠  Mode scraping seul activé")
    JobOffer = None
    SessionLocal = None

class PortalJobScraper:
    def __init__(self, use_database=True):
        self.base_url = "https://www.portaljob-madagascar.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 SafeAI-Hackathon/1.0',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.use_database = use_database and JobOffer is not None
        print(f"🤖 PortalJob Scraper initialisé (MySQL: {self.use_database})")
    
    def fetch_page(self, url):
        """Récupérer une page HTML avec retry"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    response.encoding = 'utf-8'
                    return response.text
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⏳ Tentative {attempt + 1}/{max_retries} échouée: {e}")
                    time.sleep(2)
                else:
                    print(f"❌ Erreur pour {url}: {e}")
        return None
    
    def scrape_page(self, page_num=1):
        """Scraper une page spécifique"""
        if page_num == 1:
            url = f"{self.base_url}/emploi/liste"
        else:
            url = f"{self.base_url}/emploi/liste/page/{page_num}"
        
        html = self.fetch_page(url)
        if not html:
            return []
        
        return self.extract_job_details(html, page_num)
    
    def extract_job_details(self, html_content, page_num):
        """Extraire les détails des offres"""
        soup = BeautifulSoup(html_content, 'html.parser')
        job_articles = soup.find_all('article', class_='item_annonce')
        
        job_listings = []
        
        for i, job in enumerate(job_articles, 1):
            try:
                job_data = {'source': 'portaljob'}
                
                # Titre
                title_elem = job.find('h3').find('a')
                if title_elem:
                    job_data['title'] = title_elem.text.strip()[:200]
                    job_data['link'] = title_elem.get('href', '')[:500]
                
                # Entreprise
                company_elem = job.find('h4')
                job_data['company'] = company_elem.text.strip()[:100] if company_elem else 'Non spécifié'
                
                # Type de contrat
                contract_elem = job.find('h5')
                job_data['contract_type'] = contract_elem.text.strip()[:50] if contract_elem else 'Non spécifié'
                
                # Description
                desc_elem = job.find('a', class_='description')
                if desc_elem:
                    desc_text = desc_elem.get_text(strip=True, separator=' ')
                    if 'Date limite :' in desc_text:
                        desc_text = desc_text.split('Date limite :')[0].strip()
                    job_data['description'] = desc_text[:500]
                else:
                    job_data['description'] = ''
                
                # Date
                date_elem = job.find('aside', class_='date_annonce')
                if date_elem:
                    if job.has_attr('class') and 'prem' in job['class']:
                        job_data['date_posted'] = self.clean_date("Aujourd'hui")
                    else:
                        day = date_elem.find('b')
                        month = date_elem.find('span', class_='mois')
                        year = date_elem.find('span', class_='annee')
                        if day and month and year:
                            date_str = f"{day.text.strip()} {month.text.strip()} {year.text.strip()}"
                            job_data['date_posted'] = self.clean_date(date_str)
                        else:
                            job_data['date_posted'] = self.clean_date(None)
                else:
                    job_data['date_posted'] = self.clean_date(None)
                
                # Date limite
                deadline_elem = job.find('i', class_='date_lim')
                if deadline_elem:
                    deadline_text = deadline_elem.text.strip().replace('Date limite : ', '')
                    job_data['deadline'] = self.parse_deadline(deadline_text)
                else:
                    job_data['deadline'] = None
                
                # Urgent
                urgent_elem = job.find('div', class_='urgent_flag')
                job_data['is_urgent'] = urgent_elem is not None
                
                # Secteur
                job_data['sector'] = self.extract_sector(job)
                
                # Métier
                job_data['job_title'] = job_data.get('title', '')[:100]
                
                # Localisation
                job_data['location'] = self.extract_location(job) or 'Antananarivo'
                
                # Risque IA
                ia_risk_score = self.calculate_ia_risk(
                    job_data.get('title', ''),
                    job_data.get('job_title', ''),
                    job_data.get('sector', ''),
                    job_data.get('contract_type', '')
                )
                job_data['ia_risk_score'] = ia_risk_score
                job_data['ia_risk_level'] = self.get_risk_level(ia_risk_score)
                
                # Suggestions
                suggestions = self.get_reconversion_suggestions(
                    job_data.get('job_title', ''),
                    job_data.get('sector', ''),
                    ia_risk_score
                )
                job_data['suggestions'] = ', '.join(suggestions) if suggestions else ''
                
                # Timestamps
                job_data['scraped_at'] = datetime.now()
                job_data['is_active'] = True
                
                job_listings.append(job_data)
                
            except Exception as e:
                print(f"⚠ Erreur offre {i}: {e}")
                continue
        
        return job_listings
    
    def extract_sector(self, job_element):
        """Extraire le secteur"""
        sector_keywords = {
            'informatique': 'Informatique / web',
            'commercial': 'Commercial / Vente',
            'rh': 'Management / RH',
            'marketing': 'Marketing / Communication',
            'comptabilité': 'Gestion / Comptabilité / Finance',
            'ingénieur': 'Ingénierie / industrie / BTP',
            'santé': 'Medecine / Santé',
            'enseignement': 'Enseignement',
            'droit': 'Droit / Juriste',
            'tourisme': 'Tourisme / Voyage',
            'logistique': 'Logistique / Achats',
            'agriculture': 'Agronomie / Agriculture',
        }
        
        try:
            title = job_element.find('h3').text.lower() if job_element.find('h3') else ''
            desc = job_element.find('a', class_='description').text.lower() if job_element.find('a', class_='description') else ''
            
            text_to_check = title + ' ' + desc
            
            for keyword, sector in sector_keywords.items():
                if keyword in text_to_check:
                    return sector
            
            return 'Non spécifié'
        except:
            return 'Non spécifié'
    
    def extract_location(self, job_element):
        """Extraire la localisation"""
        # PortalJob ne montre pas souvent la localisation, donc on garde Antananarivo par défaut
        return 'Antananarivo'
    
    def clean_date(self, date_str):
        """Nettoyer la date"""
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d")
        
        date_str = date_str.strip().lower()
        
        if "aujourd'hui" in date_str:
            return datetime.now().strftime("%Y-%m-%d")
        elif "hier" in date_str:
            return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Tenter de parser "06 Déc 2025"
        try:
            month_mapping = {
                'jan': '01', 'fév': '02', 'mar': '03', 'avr': '04',
                'mai': '05', 'juin': '06', 'juil': '07', 'aoû': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'déc': '12',
            }
            
            pattern = r'(\d{1,2})\s+([a-zA-ZÀ-ÿ]+)\s+(\d{4})'
            match = re.search(pattern, date_str)
            
            if match:
                day = match.group(1).zfill(2)
                month_fr = match.group(2).lower()[:3]
                year = match.group(3)
                
                month = month_mapping.get(month_fr, '01')
                return f"{year}-{month}-{day}"
        except:
            pass
        
        return datetime.now().strftime("%Y-%m-%d")
    
    def parse_deadline(self, deadline_str):
        """Parser la date limite"""
        if not deadline_str:
            return None
        
        try:
            parts = deadline_str.split('/')
            if len(parts) == 3:
                day, month, year = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            pass
        
        return None
    
    def calculate_ia_risk(self, title, metier, secteur, contrat):
        """Calculer le risque IA"""
        score = 5.0
        text = f"{title} {metier} {secteur} {contrat}".lower()
        
        metier_risks = {
            'chauffeur': 9.0, 'conducteur': 9.0,
            'livreur': 8.5, 'coursier': 8.5,
            'caissier': 8.0,
            'téléopérateur': 7.5, 'call center': 7.5,
            'secrétaire': 7.0, 'assistant': 6.5,
            'opérateur': 7.0,
            'mécanicien': 6.0,
            'comptable': 5.0,
            'enseignant': 2.0, 'professeur': 2.0,
            'médecin': 1.5,
            'infirmier': 2.0,
            'développeur': 3.0,
            'manager': 2.5, 'directeur': 2.0,
            'coordinateur': 2.0,
            'conseiller': 3.0,
        }
        
        for job, risk in metier_risks.items():
            if job in text:
                score = risk
                break
        
        return round(max(1.0, min(10.0, score)), 1)
    
    def get_risk_level(self, score):
        """Convertir score en niveau"""
        if score >= 8.0:
            return "Élevé"
        elif score >= 5.0:
            return "Moyen"
        else:
            return "Faible"
    
    def get_reconversion_suggestions(self, metier, secteur, score):
        """Générer suggestions"""
        if score >= 8.0:
            return [
                "Formation en compétences numériques avancées",
                "Reconversion vers la supervision d'équipe",
                "Apprentissage des outils d'automatisation"
            ]
        elif score >= 5.0:
            return [
                "Renforcement des compétences en analyse",
                "Apprentissage des outils digitaux du secteur",
                "Spécialisation en valeur ajoutée"
            ]
        else:
            return [
                "Continuer formation dans votre domaine",
                "Développer une spécialisation complémentaire",
                "Renforcer compétences en leadership"
            ]
    
    def save_to_database(self, offer_data):
        """Sauvegarder en base avec vérification par source"""
        if not self.use_database:
            return False
        
        try:
            db = SessionLocal()
            
            # Vérifier si offre existe (même lien OU titre+entreprise de même source)
            existing = db.query(JobOffer).filter(
                (JobOffer.link == offer_data['link']) &
                (JobOffer.source == offer_data['source'])
            ).first()
            
            if not existing:
                job_offer = JobOffer(
                    title=offer_data['title'],
                    link=offer_data['link'],
                    company=offer_data['company'],
                    date_posted=offer_data['date_posted'],
                    contract_type=offer_data['contract_type'],
                    sector=offer_data['sector'],
                    job_title=offer_data['job_title'],
                    location=offer_data['location'],
                    description=offer_data['description'],
                    deadline=offer_data.get('deadline'),
                    is_urgent=offer_data.get('is_urgent', False),
                    ia_risk_score=offer_data['ia_risk_score'],
                    ia_risk_level=offer_data['ia_risk_level'],
                    suggestions=offer_data['suggestions'],
                    scraped_at=datetime.now(),
                    is_active=True,
                    source=offer_data['source']
                )
                db.add(job_offer)
                db.commit()
                db.close()
                return True
            else:
                db.close()
                return False
                
        except Exception as e:
            print(f"❌ Erreur DB: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return False
    
    def scrape(self, pages=10):
        """Scraper principal"""
        print(f"\n{'='*60}")
        print(f"📥 SCRAPING PORTALJOB")
        print(f"Pages: {pages}")
        print(f"{'='*60}")
        
        all_offers = []
        saved_count = 0
        
        for page in range(1, pages + 1):
            try:
                print(f"\n📄 Page {page}/{pages}")
                
                offers = self.scrape_page(page)
                
                if not offers:
                    print(f"   ⚠  Aucune offre")
                    continue
                
                page_saved = 0
                for offer in offers:
                    all_offers.append(offer)
                    if self.save_to_database(offer):
                        page_saved += 1
                        saved_count += 1
                
                print(f"   ✅ {page_saved} nouvelles offres")
                
                if page < pages:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ Erreur page {page}: {e}")
                continue
        
        # Résumé
        if all_offers:
            print(f"\n{'='*60}")
            print(f"📊 RÉSULTATS PORTALJOB")
            print(f"{'='*60}")
            print(f"   • Pages: {pages}")
            print(f"   • Offres analysées: {len(all_offers)}")
            print(f"   • Nouvelles offres (source='portaljob'): {saved_count}")
            
            # Statistiques
            risk_counts = {"Élevé": 0, "Moyen": 0, "Faible": 0}
            for offer in all_offers:
                level = offer.get('ia_risk_level', 'Inconnu')
                if level in risk_counts:
                    risk_counts[level] += 1
            
            print(f"\n📈 RISQUES IA:")
            for level, count in risk_counts.items():
                percentage = (count / len(all_offers) * 100) if all_offers else 0
                print(f"   • {level}: {count} ({percentage:.1f}%)")
        
        return all_offers

def main():
    """Fonction principale"""
    print("\n" + "="*60)
    print("🤖 PORTALJOB SCRAPER - INTÉGRATION COMPLÈTE")
    print("="*60)
    
    # Tester la connexion MySQL
    try:
        if JobOffer:
            db = SessionLocal()
            count = db.query(JobOffer).count()
            db.close()
            print(f"✅ MySQL connecté ({count} offres total)")
        else:
            print("⚠  MySQL non disponible")
    except Exception as e:
        print(f"❌ Erreur MySQL: {e}")
    
    # Config
    use_mysql = True if JobOffer else False
    scraper = PortalJobScraper(use_database=use_mysql)
    
    # Lancer le scraping
    offers = scraper.scrape(pages=10)
    
    # Résumé final
    print(f"\n{'='*60}")
    print(f"🎉 PORTALJOB TERMINÉ!")
    print(f"{'='*60}")
    
    if offers:
        print(f"📊 Total: {len(offers)} offres analysées")
        
        # Vérifier en base
        if use_mysql:
            try:
                db = SessionLocal()
                portaljob_count = db.query(JobOffer).filter(JobOffer.source == 'portaljob').count()
                asako_count = db.query(JobOffer).filter(JobOffer.source == 'asako').count()
                db.close()
                
                print(f"📦 En base de données:")
                print(f"   • Source 'portaljob': {portaljob_count} offres")
                print(f"   • Source 'asako': {asako_count} offres")
                print(f"   • Total: {portaljob_count + asako_count} offres")
            except:
                pass
    
    print(f"\n✨ Scraping terminé à {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()