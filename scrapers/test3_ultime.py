#!/usr/bin/env python3
"""
PortalJob Madagascar Scraper - Intégration directe avec MySQL
Objectif: Scraper les offres d'emploi de PortalJob et les insérer dans la base de données
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import time
import sys
import os
import json

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
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
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
                print(f"📡 Récupération: {url}")
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    response.encoding = 'utf-8'
                    print(f"✅ Page chargée avec succès")
                    return response.text
                else:
                    print(f"⚠  Statut {response.status_code} pour {url}")
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⏳ Tentative {attempt + 1}/{max_retries} échouée: {e}")
                    time.sleep(2)
                else:
                    print(f"❌ Erreur après {max_retries} tentatives: {e}")
        return None
    
    def scrape_page(self, page_num=1):
        """Scraper une page spécifique de PortalJob"""
        if page_num == 1:
            url = f"{self.base_url}/emploi/liste"
        else:
            url = f"{self.base_url}/emploi/liste/page/{page_num}"
        
        html = self.fetch_page(url)
        if not html:
            return []
        
        return self.extract_job_details_from_html(html, page_num)
    
    def extract_job_details_from_html(self, html_content, page_num=1):
        """Extrait les détails des offres d'emploi depuis le HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Trouver tous les articles d'offres d'emploi
        job_articles = soup.find_all('article', class_='item_annonce')
        
        job_listings = []
        
        print(f"📊 {len(job_articles)} offres détectées sur la page {page_num}")
        
        for i, job in enumerate(job_articles, 1):
            try:
                job_data = {}
                
                # Titre de l'offre
                title_elem = job.find('h3').find('a')
                if title_elem:
                    job_data['title'] = title_elem.text.strip()
                    job_data['link'] = title_elem.get('href', '')
                
                # Nom de l'entreprise
                company_elem = job.find('h4')
                if company_elem:
                    job_data['company'] = company_elem.text.strip()
                else:
                    job_data['company'] = 'Non spécifié'
                
                # Type de contrat
                contract_elem = job.find('h5')
                if contract_elem:
                    job_data['contract_type'] = contract_elem.text.strip()
                else:
                    job_data['contract_type'] = 'Non spécifié'
                
                # Description (extrait)
                desc_elem = job.find('a', class_='description')
                if desc_elem:
                    desc_text = desc_elem.get_text(strip=True, separator=' ')
                    if 'Date limite :' in desc_text:
                        desc_text = desc_text.split('Date limite :')[0].strip()
                    job_data['description'] = desc_text[:500]  # Limiter la longueur
                else:
                    job_data['description'] = ''
                
                # Date de publication
                date_elem = job.find('aside', class_='date_annonce').find('div', class_='date')
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
                date_lim_elem = job.find('i', class_='date_lim')
                if date_lim_elem:
                    date_lim_text = date_lim_elem.text.strip().replace('Date limite : ', '')
                    job_data['deadline'] = self.parse_deadline(date_lim_text)
                else:
                    job_data['deadline'] = None
                
                # Offre urgente
                urgent_elem = job.find('div', class_='urgent_flag')
                job_data['is_urgent'] = True if urgent_elem else False
                
                # Secteur d'activité
                job_data['sector'] = self.extract_sector_from_context(job)
                
                # Référence
                job_data['reference'] = self.extract_reference(job_data.get('title', ''))
                
                # Métier (similaire au titre)
                job_data['job_title'] = job_data.get('title', '')[:100]
                
                # Localisation (par défaut Antananarivo)
                job_data['location'] = 'Antananarivo'
                
                # Calculer le risque IA
                ia_risk_score = self.calculate_ia_risk(
                    job_data['title'], 
                    job_data['job_title'], 
                    job_data['sector'], 
                    job_data['contract_type']
                )
                job_data['ia_risk_score'] = ia_risk_score
                job_data['ia_risk_level'] = self.get_risk_level(ia_risk_score)
                
                # Suggestions de reconversion
                suggestions = self.get_reconversion_suggestions(
                    job_data['job_title'], 
                    job_data['sector'], 
                    ia_risk_score
                )
                job_data['suggestions'] = ', '.join(suggestions)
                
                # Timestamp
                job_data['scraped_at'] = datetime.now()
                job_data['is_active'] = True
                
                job_listings.append(job_data)
                
                if i % 5 == 0:
                    print(f"   ✓ {i}/{len(job_articles)} offres analysées")
                
            except Exception as e:
                print(f"⚠ Erreur parsing offre {i}: {e}")
                continue
        
        return job_listings
    
    def extract_sector_from_context(self, job_element):
        """Extrait le secteur d'activité à partir du contexte"""
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
            'bâtiment': 'Ingénierie / industrie / BTP',
            'btp': 'Ingénierie / industrie / BTP',
            'banque': 'Gestion / Comptabilité / Finance',
            'finance': 'Gestion / Comptabilité / Finance',
            'call center': 'Conseiller client / Call center',
            'téléconseiller': 'Conseiller client / Call center',
            'service client': 'Conseiller client / Call center',
            'stage': 'Stage',
            'stagiaire': 'Stage',
            'freelance': 'Free-lance',
            'cdi': 'CDI',
            'cdd': 'CDD'
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
    
    def extract_reference(self, title):
        """Extrait la référence de l'offre depuis le titre"""
        patterns = [
            r'ref[:\s]*([A-Z0-9\-_/]+)',
            r'réf[:\s]*([A-Z0-9\-_/]+)',
            r'reference[:\s]*([A-Z0-9\-_/]+)',
            r'-([A-Z0-9\-_/]+)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def clean_date(self, date_str):
        """Nettoyer et formater la date pour MySQL"""
        if not date_str or date_str == "Non spécifié":
            return datetime.now().strftime("%Y-%m-%d")
        
        date_str = date_str.strip().lower()
        
        # Formats spécifiques à PortalJob
        if "aujourd'hui" in date_str or "today" in date_str:
            return datetime.now().strftime("%Y-%m-%d")
        elif "hier" in date_str or "yesterday" in date_str:
            return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Tenter de parser les dates du style "06 Déc 2025"
        try:
            # Mapping des mois français
            month_mapping = {
                'jan': '01', 'fév': '02', 'mar': '03', 'avr': '04',
                'mai': '05', 'juin': '06', 'juil': '07', 'aoû': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'déc': '12',
                'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
                'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
                'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
            }
            
            # Pattern pour "06 Déc 2025"
            pattern = r'(\d{1,2})\s+([a-zA-ZÀ-ÿ]+)\s+(\d{4})'
            match = re.search(pattern, date_str)
            
            if match:
                day = match.group(1).zfill(2)
                month_fr = match.group(2).lower()[:3]  # Prendre les 3 premiers caractères
                year = match.group(3)
                
                month = month_mapping.get(month_fr, '01')
                
                return f"{year}-{month}-{day}"
        except:
            pass
        
        # Fallback à aujourd'hui
        return datetime.now().strftime("%Y-%m-%d")
    
    def parse_deadline(self, deadline_str):
        """Parser la date limite"""
        if not deadline_str or deadline_str == "Non spécifiée":
            return None
        
        try:
            # Format "20/12/2025"
            parts = deadline_str.split('/')
            if len(parts) == 3:
                day, month, year = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            pass
        
        return None
    
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
            'opérateur': 7.0, 'operator': 7.0, 'annotateur': 8.0,
            'mécanicien': 6.0, 'mechanic': 6.0,
            'comptable': 5.0, 'accountant': 5.0, 'analyste': 4.0,
            'enseignant': 2.0, 'teacher': 2.0, 'professeur': 2.0,
            'médecin': 1.5, 'doctor': 1.5,
            'infirmier': 2.0, 'nurse': 2.0,
            'développeur': 3.0, 'developer': 3.0, 'programmeur': 3.0,
            'manager': 2.5, 'directeur': 2.0, 'chef': 2.5,
            'coordinateur': 2.0, 'coordinator': 2.0,
            'conseiller': 3.0, 'consultant': 3.0, 'responsable': 2.5,
            'ingénieur': 3.5, 'engineer': 3.5,
            'technico-commercial': 4.0, 'commercial': 4.0,
            'chargé': 3.0, 'chargee': 3.0,
            'stagiaire': 6.0, 'stage': 6.0,
            'freelance': 3.5, 'free-lance': 3.5,
        }
        
        for job, risk in metier_risks.items():
            if job in text:
                score = risk
                break  # Prendre le premier métier trouvé
        
        # Ajustements par secteur
        if any(word in text for word in ['transport', 'logistique', 'delivery']):
            score += 1.0
        if any(word in text for word in ['industrie', 'production', 'manufacturing', 'usine']):
            score += 1.5
        if any(word in text for word in ['commerce', 'retail', 'supermarket', 'vente']):
            score += 0.5
        if any(word in text for word in ['technologie', 'tech', 'it', 'informatique', 'symfony', 'web']):
            score -= 1.0
        if any(word in text for word in ['santé', 'health', 'medical', 'médical']):
            score -= 1.5
        if any(word in text for word in ['éducation', 'education', 'formation', 'enseignement']):
            score -= 1.0
        if any(word in text for word in ['finance', 'banque', 'comptabilité', 'financier']):
            score += 0.5
        if any(word in text for word in ['marketing', 'communication', 'publicité']):
            score += 0.5
        
        # Ajustements par mots-clés
        high_risk_words = ['répétitif', 'routine', 'standard', 'process', 'assembly', 'saisie', 'data entry']
        for word in high_risk_words:
            if word in text:
                score += 0.5
        
        low_risk_words = ['créatif', 'creative', 'design', 'gestion', 'management', 'relation client', 'leadership', 'stratégie']
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
                "Formation en compétences numériques avancées",
                "Reconversion vers la supervision ou coordination d'équipe",
                "Développement de compétences en gestion de projet agile",
                "Apprentissage des outils d'automatisation et d'IA"
            ]
        elif score >= 5.0:  # Risque moyen
            suggestions = [
                "Renforcement des compétences en analyse de données",
                "Apprentissage des outils digitaux spécifiques au secteur",
                "Spécialisation dans un créneau à forte valeur ajoutée",
                "Développement de compétences interpersonnelles avancées"
            ]
        else:  # Risque faible
            suggestions = [
                "Continuer à se former dans son domaine d'expertise",
                "Développer une spécialisation complémentaire",
                "Renforcer les compétences en leadership et innovation",
                "Apprentissage des dernières technologies du secteur"
            ]
        
        return suggestions
    
    def save_to_database(self, offer_data):
        """Sauvegarder une offre en base de données"""
        if not self.use_database:
            print(f"  ⚠  MySQL désactivé, offre non sauvegardée: {offer_data.get('title', '')[:50]}...")
            return False
        
        try:
            db = SessionLocal()
            
            # Vérifier si l'offre existe déjà (par lien ou titre+entreprise)
            existing = db.query(JobOffer.id).filter(
                (JobOffer.link == offer_data['link']) |
                ((JobOffer.title == offer_data['title']) & 
                 (JobOffer.company == offer_data['company']))
            ).first()
            
            if not existing:
                # Créer une nouvelle offre
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
                    deadline=offer_data['deadline'],
                    is_urgent=offer_data['is_urgent'],
                    reference=offer_data['reference'],
                    ia_risk_score=offer_data['ia_risk_score'],
                    ia_risk_level=offer_data['ia_risk_level'],
                    suggestions=offer_data['suggestions'],
                    scraped_at=datetime.now(),
                    is_active=True,
                    source="portaljob"  # Marquer la source
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
    
    def scrape_multiple_pages(self, num_pages=20):
        """Scraper plusieurs pages d'offres"""
        print(f"\n{'='*60}")
        print(f"📥 SCRAPING PORTALJOB MADAGASCAR")
        print(f"Objectif: {num_pages} pages (~{num_pages * 20} offres)")
        print(f"{'='*60}")
        
        all_offers = []
        saved_count = 0
        skipped_count = 0
        
        for page in range(1, num_pages + 1):
            try:
                print(f"\n📄 Page {page}/{num_pages}")
                
                offers = self.scrape_page(page)
                
                if not offers:
                    print(f"   ⚠  Aucune offre sur cette page, on continue...")
                    continue
                
                page_saved = 0
                page_skipped = 0
                
                for offer in offers:
                    if offer.get('link'):
                        all_offers.append(offer)
                        
                        if self.use_database:
                            if self.save_to_database(offer):
                                page_saved += 1
                                saved_count += 1
                            else:
                                page_skipped += 1
                                skipped_count += 1
                
                print(f"   ✅ {page_saved} nouvelles offres sauvegardées")
                if page_skipped > 0:
                    print(f"   ⏭️  {page_skipped} offres déjà existantes")
                
                # Pause entre les pages pour respecter le serveur
                if page < num_pages:
                    sleep_time = 1.5 if page % 5 == 0 else 0.8  # Pause plus longue toutes les 5 pages
                    time.sleep(sleep_time)
                    
            except Exception as e:
                print(f"❌ Erreur page {page}: {e}")
                continue
        
        # Afficher le résumé
        if all_offers:
            print(f"\n{'='*60}")
            print(f"📊 RÉSULTATS PORTALJOB SCRAPING")
            print(f"{'='*60}")
            print(f"   • Pages analysées: {num_pages}")
            print(f"   • Offres analysées: {len(all_offers)}")
            print(f"   • Nouvelles offres en MySQL: {saved_count}")
            print(f"   • Offres déjà existantes: {skipped_count}")
            
            # Statistiques de risque
            risk_counts = {"Élevé": 0, "Moyen": 0, "Faible": 0}
            companies = {}
            
            for offer in all_offers:
                level = offer.get('ia_risk_level', 'Inconnu')
                if level in risk_counts:
                    risk_counts[level] += 1
                
                company = offer.get('company', 'Inconnu')
                companies[company] = companies.get(company, 0) + 1
            
            print(f"\n📈 DISTRIBUTION DES RISQUES IA:")
            for level, count in risk_counts.items():
                percentage = (count / len(all_offers) * 100) if all_offers else 0
                print(f"   • {level}: {count} offres ({percentage:.1f}%)")
            
            print(f"\n🏢 TOP 5 ENTREPRISES RECRUTEUSES:")
            top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (company, count) in enumerate(top_companies, 1):
                print(f"   {i}. {company}: {count} offres")
            
            # Exemples d'offres à haut risque
            high_risk_offers = [o for o in all_offers if o.get('ia_risk_level') == 'Élevé']
            if high_risk_offers:
                print(f"\n🚨 EXEMPLES À HAUT RISQUE D'AUTOMATISATION:")
                for i, example in enumerate(high_risk_offers[:3], 1):
                    print(f"   {i}. {example['title'][:60]}...")
                    print(f"      Entreprise: {example['company']}")
                    print(f"      Score IA: {example['ia_risk_score']}/10")
        
        return {
            'total_offers': len(all_offers),
            'saved_to_db': saved_count,
            'already_exist': skipped_count,
            'offers': all_offers
        }
    
    def export_to_json(self, offers, filename=None):
        """Exporter les offres en JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"portaljob_offres_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(offers, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"💾 Offres exportées vers: {filename}")
            return True
        except Exception as e:
            print(f"❌ Erreur export JSON: {e}")
            return False

def main():
    """Fonction principale"""
    print("\n" + "="*60)
    print("🤖 PORTALJOB MADAGASCAR SCRAPER")
    print("Scraping direct vers MySQL")
    print("="*60)
    
    # Vérifier la connexion MySQL
    try:
        if JobOffer:
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            print("✅ Connexion MySQL active")
        else:
            print("⚠  MySQL non disponible - mode export JSON uniquement")
    except Exception as e:
        print(f"❌ Erreur connexion MySQL: {e}")
        print("⚠  Continuation en mode scraping seul")
    
    # Configuration
    use_mysql = True if JobOffer else False
    scraper = PortalJobScraper(use_database=use_mysql)
    
    print("\n📋 CONFIGURATION:")
    print(f"   • Source: PortalJob Madagascar")
    print(f"   • URL: {scraper.base_url}/emploi/liste")
    print(f"   • MySQL: {'Activé' if use_mysql else 'Désactivé'}")
    
    # Demander le nombre de pages
    try:
        num_pages_input = input("\n🔢 Nombre de pages à scraper (1-20, défaut: 10): ").strip()
        if num_pages_input:
            num_pages = min(max(1, int(num_pages_input)), 20)
        else:
            num_pages = 10
    except:
        num_pages = 10
    
    print(f"\n🎯 LANCEMENT DU SCRAPING DE {num_pages} PAGES...")
    
    # Lancer le scraping
    results = scraper.scrape_multiple_pages(num_pages)
    
    # Résumé final
    print(f"\n{'='*60}")
    print(f"🎉 SCRAPING TERMINÉ AVEC SUCCÈS!")
    print(f"{'='*60}")
    print(f"📊 STATISTIQUES FINALES:")
    print(f"   • Offres analysées: {results['total_offers']}")
    
    if scraper.use_database:
        print(f"   • Nouvelles offres en MySQL: {results['saved_to_db']}")
        print(f"   • Offres déjà existantes: {results['already_exist']}")
    
    # Exporter en JSON aussi
    export_json = input("\n💾 Exporter les offres en JSON également? (o/n): ").strip().lower()
    if export_json == 'o':
        scraper.export_to_json(results['offers'])
    
    print(f"\n🎯 PROCHAINES ÉTAPES:")
    if scraper.use_database:
        print("1. Vérifier la base de données: SELECT COUNT(*) FROM job_offers WHERE source='portaljob';")
        print("2. Démarrer l'API: python3 run.py")
        print("3. Tester l'API: curl http://localhost:5000/api/offers?source=portaljob")
    else:
        print("1. Les données sont dans le fichier JSON exporté")
        print("2. Vous pouvez les importer manuellement dans MySQL")
    
    print(f"\n✨ Opération terminée à {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()