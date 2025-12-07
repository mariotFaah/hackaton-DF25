#!/usr/bin/env python3
"""
PortalJob Madagascar Scraper - Version simplifiée pour MySQL
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import time
import mysql.connector
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class PortalJobScraper:
    def __init__(self):
        self.base_url = "https://www.portaljob-madagascar.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Connexion directe à MySQL (comme AsakoScraper)
        self.db = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'safe_ai_hackathon'),
            charset='utf8mb4'
        )
        self.cursor = self.db.cursor(dictionary=True)
        print("✅ Connecté à MySQL (style Asako)")
    
    def fetch_page(self, url):
        """Récupérer une page HTML"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"📡 Récupération: {url}")
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    response.encoding = 'utf-8'
                    print(f"✅ Page chargée")
                    return response.text
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⏳ Tentative {attempt + 1} échouée: {e}")
                    time.sleep(2)
                else:
                    print(f"❌ Erreur: {e}")
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
        
        return self.extract_jobs(html)
    
    def extract_jobs(self, html):
        """Extraire les offres d'emploi"""
        soup = BeautifulSoup(html, 'html.parser')
        job_articles = soup.find_all('article', class_='item_annonce')
        
        jobs = []
        print(f"📊 {len(job_articles)} offres détectées")
        
        for job in job_articles:
            job_data = self.extract_job_data(job)
            if job_data:
                jobs.append(job_data)
        
        return jobs
    
    def extract_job_data(self, job):
        """Extraire les données d'une offre"""
        try:
            # Titre
            title_elem = job.find('h3').find('a')
            if not title_elem:
                return None
            
            title = title_elem.text.strip()
            link = title_elem.get('href', '')
            
            # Entreprise
            company_elem = job.find('h4')
            company = company_elem.text.strip() if company_elem else 'Non spécifié'
            
            # Contrat
            contract_elem = job.find('h5')
            contract = contract_elem.text.strip() if contract_elem else 'Non spécifié'
            
            # Description
            desc_elem = job.find('a', class_='description')
            description = ''
            if desc_elem:
                desc_text = desc_elem.get_text(strip=True, separator=' ')
                if 'Date limite :' in desc_text:
                    desc_text = desc_text.split('Date limite :')[0].strip()
                description = desc_text[:500]
            
            # Date de publication
            date_str = "Aujourd'hui"
            if job.has_attr('class') and 'prem' in job['class']:
                date_str = "Aujourd'hui"
            else:
                date_elem = job.find('div', class_='date')
                if date_elem:
                    day = date_elem.find('b')
                    month = date_elem.find('span', class_='mois')
                    year = date_elem.find('span', class_='annee')
                    if day and month and year:
                        date_str = f"{day.text.strip()} {month.text.strip()} {year.text.strip()}"
            
            # Date limite
            deadline = None
            date_lim_elem = job.find('i', class_='date_lim')
            if date_lim_elem:
                deadline_text = date_lim_elem.text.strip().replace('Date limite : ', '')
                deadline = self.parse_deadline(deadline_text)
            
            # Urgent
            urgent_elem = job.find('div', class_='urgent_flag')
            is_urgent = 1 if urgent_elem else 0
            
            # Secteur
            sector = self.extract_sector(title, description)
            
            # Métier
            job_title = self.extract_job_title(title)
            
            # Calcul du risque IA (simplifié comme Asako)
            ia_risk_score = self.calculate_ia_risk(title, job_title, sector, contract)
            ia_risk_level = self.get_risk_level(ia_risk_score)
            
            # Suggestions
            suggestions = self.get_suggestions(ia_risk_score)
            
            return {
                'title': title[:200],
                'link': link[:500],
                'company': company[:100],
                'contract_type': contract[:50],
                'sector': sector[:100],
                'job_title': job_title[:100],
                'location': 'Antananarivo',  # Par défaut
                'description': description,
                'date_posted': self.parse_date(date_str),
                'deadline': deadline,
                'is_urgent': is_urgent,
                'ia_risk_score': ia_risk_score,
                'ia_risk_level': ia_risk_level,
                'suggestions': ', '.join(suggestions),
                'source': 'portaljob'
            }
            
        except Exception as e:
            print(f"⚠ Erreur extraction: {e}")
            return None
    
    def extract_sector(self, title, description):
        """Déterminer le secteur"""
        text = f"{title} {description}".lower()
        sector_map = {
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
            'btp': 'Ingénierie / industrie / BTP',
            'banque': 'Gestion / Comptabilité / Finance',
            'call center': 'Conseiller client / Call center',
            'téléconseiller': 'Conseiller client / Call center'
        }
        
        for keyword, sector in sector_map.items():
            if keyword in text:
                return sector
        
        return 'Non spécifié'
    
    def extract_job_title(self, title):
        """Extraire le titre du poste"""
        common_titles = ['développeur', 'commercial', 'comptable', 'ingénieur',
                        'assistant', 'responsable', 'manager', 'consultant',
                        'stagiaire', 'chauffeur', 'secrétaire', 'agent']
        
        title_lower = title.lower()
        for common in common_titles:
            if common in title_lower:
                return common.title()
        
        return title.split(' ')[0] if title else 'Non spécifié'
    
    def calculate_ia_risk(self, title, job_title, sector, contract):
        """Calculer le score de risque IA"""
        score = 5.0
        text = f"{title} {job_title} {sector} {contract}".lower()
        
        # Métiers à risque élevé
        high_risk = ['chauffeur', 'conducteur', 'caissier', 'opérateur',
                    'téléopérateur', 'call center', 'secrétaire', 'agent',
                    'livreur', 'coursier', 'annotateur']
        for job in high_risk:
            if job in text:
                score += 2.0
        
        # Métiers à faible risque
        low_risk = ['développeur', 'ingénieur', 'médecin', 'enseignant',
                   'manager', 'consultant', 'analyste', 'programmeur']
        for job in low_risk:
            if job in text:
                score -= 1.5
        
        # Ajustements par secteur
        if any(word in text for word in ['transport', 'logistique', 'delivery']):
            score += 1.0
        if any(word in text for word in ['industrie', 'production']):
            score += 1.5
        if any(word in text for word in ['technologie', 'informatique']):
            score -= 1.0
        if any(word in text for word in ['santé', 'medical']):
            score -= 1.5
        
        # Garder dans les limites
        return max(1.0, min(10.0, round(score, 1)))
    
    def get_risk_level(self, score):
        """Déterminer le niveau de risque"""
        if score >= 8.0:
            return 'Élevé'
        elif score >= 5.0:
            return 'Moyen'
        else:
            return 'Faible'
    
    def get_suggestions(self, score):
        """Générer des suggestions"""
        if score >= 8.0:
            return ["Formation numérique", "Reconversion logistique", "Outils digitaux"]
        elif score >= 5.0:
            return ["Compétences digitales", "Spécialisation technique", "Gestion"]
        else:
            return ["Formation continue", "Expertise avancée", "Leadership"]
    
    def parse_date(self, date_str):
        """Parser la date"""
        try:
            if 'aujourd' in date_str.lower():
                return datetime.now().strftime('%Y-%m-%d')
            
            # Format "06 Déc 2025"
            months = {
                'jan': '01', 'fév': '02', 'mar': '03', 'avr': '04',
                'mai': '05', 'juin': '06', 'juil': '07', 'aoû': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'déc': '12'
            }
            
            match = re.search(r'(\d{1,2})\s+(\w{3})\s+(\d{4})', date_str)
            if match:
                day, month_fr, year = match.groups()
                month = months.get(month_fr.lower(), '01')
                return f"{year}-{month}-{day.zfill(2)}"
        except:
            pass
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def parse_deadline(self, deadline_str):
        """Parser la date limite"""
        try:
            # Format "20/12/2025"
            parts = deadline_str.split('/')
            if len(parts) == 3:
                day, month, year = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            pass
        return None
    
    def save_to_database(self, job_data):
        """Sauvegarder dans la base de données"""
        try:
            # Vérifier si l'offre existe déjà
            check_query = """
            SELECT id FROM job_offers 
            WHERE link = %s OR (title = %s AND company = %s)
            """
            self.cursor.execute(check_query, (job_data['link'], job_data['title'], job_data['company']))
            existing = self.cursor.fetchone()
            
            if existing:
                print(f"⏩ Déjà existant: {job_data['title'][:50]}...")
                return False
            
            # Insérer la nouvelle offre
            insert_query = """
            INSERT INTO job_offers (
                title, link, company, contract_type, sector, job_title,
                location, description, date_posted, deadline, is_urgent,
                ia_risk_score, ia_risk_level, suggestions, source,
                scraped_at, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            """
            
            values = (
                job_data['title'],
                job_data['link'],
                job_data['company'],
                job_data['contract_type'],
                job_data['sector'],
                job_data['job_title'],
                job_data['location'],
                job_data['description'],
                job_data['date_posted'],
                job_data['deadline'],
                job_data['is_urgent'],
                job_data['ia_risk_score'],
                job_data['ia_risk_level'],
                job_data['suggestions'],
                job_data['source'],
                datetime.now()
            )
            
            self.cursor.execute(insert_query, values)
            self.db.commit()
            print(f"💾 Sauvegardé: {job_data['title'][:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Erreur base de données: {e}")
            self.db.rollback()
            return False
    
    def scrape(self, pages=20):
        """Exécuter le scraping"""
        print(f"\n🎯 Scraping PortalJob ({pages} pages)...")
        
        total_jobs = 0
        saved_jobs = 0
        
        for page in range(1, pages + 1):
            print(f"\n📄 Page {page}/{pages}")
            jobs = self.scrape_page(page)
            
            if not jobs:
                print("   ⚠  Aucune offre trouvée")
                continue
            
            page_saved = 0
            for job in jobs:
                if self.save_to_database(job):
                    page_saved += 1
                    saved_jobs += 1
            
            total_jobs += len(jobs)
            print(f"   ✅ {len(jobs)} offres analysées, {page_saved} nouvelles")
            
            # Pause entre les pages
            if page < pages:
                time.sleep(1)
        
        # Résumé
        print(f"\n{'='*60}")
        print(f"📊 RÉSULTATS PORTALJOB")
        print(f"{'='*60}")
        print(f"   • Pages analysées: {pages}")
        print(f"   • Offres analysées: {total_jobs}")
        print(f"   • Nouvelles offres sauvegardées: {saved_jobs}")
        
        # Fermer la connexion
        self.cursor.close()
        self.db.close()
        
        return saved_jobs

def main():
    """Fonction principale"""
    print("\n" + "="*60)
    print("🤖 PORTALJOB MADAGASCAR SCRAPER")
    print("Version simplifiée pour MySQL")
    print("="*60)
    
    # Créer le scraper
    scraper = PortalJobScraper()
    
    # Nombre de pages à scraper
    try:
        num_pages = 20  # Vous pouvez ajuster ce nombre
    except:
        num_pages = 10
    
    print(f"\n🎯 LANCEMENT DU SCRAPING DE {num_pages} PAGES...")
    
    # Lancer le scraping
    saved_count = scraper.scrape(pages=num_pages)
    
    print(f"\n✨ Terminé! {saved_count} nouvelles offres PortalJob ajoutées à la base.")

if __name__ == "__main__":
    main()