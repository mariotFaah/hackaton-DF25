import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time
import json

class PortalJobScraper:
    def __init__(self):
        self.base_url = "https://www.portaljob-madagascar.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def extract_job_details_from_html(self, html_content):
        """Extrait les détails des offres d'emploi depuis le HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Trouver tous les articles d'offres d'emploi
        job_articles = soup.find_all('article', class_='item_annonce')
        
        job_listings = []
        
        for job in job_articles:
            try:
                job_data = {}
                
                # Titre de l'offre
                title_elem = job.find('h3').find('a')
                if title_elem:
                    job_data['titre'] = title_elem.text.strip()
                    job_data['lien'] = title_elem.get('href', '')
                
                # Nom de l'entreprise
                company_elem = job.find('h4')
                if company_elem:
                    job_data['entreprise'] = company_elem.text.strip()
                
                # Type de contrat
                contract_elem = job.find('h5')
                if contract_elem:
                    job_data['contrat'] = contract_elem.text.strip()
                
                # Description (extrait)
                desc_elem = job.find('a', class_='description')
                if desc_elem:
                    # Prendre tout le texte sauf la date limite
                    desc_text = desc_elem.get_text(strip=True, separator=' ')
                    # Retirer la partie date limite si présente
                    if 'Date limite :' in desc_text:
                        desc_text = desc_text.split('Date limite :')[0].strip()
                    job_data['description'] = desc_text
                
                # Date de publication
                date_elem = job.find('aside', class_='date_annonce').find('div', class_='date')
                if date_elem:
                    # Vérifier si c'est une offre "prem" (du jour)
                    if job.has_attr('class') and 'prem' in job['class']:
                        job_data['date_publication'] = "Aujourd'hui"
                    else:
                        day = date_elem.find('b')
                        month = date_elem.find('span', class_='mois')
                        year = date_elem.find('span', class_='annee')
                        if day and month and year:
                            job_data['date_publication'] = f"{day.text.strip()} {month.text.strip()} {year.text.strip()}"
                
                # Date limite
                date_lim_elem = job.find('i', class_='date_lim')
                if date_lim_elem:
                    job_data['date_limite'] = date_lim_elem.text.strip().replace('Date limite : ', '')
                
                # Logo de l'entreprise (optionnel - à retirer si non nécessaire)
                logo_elem = job.find('img')
                if logo_elem:
                    job_data['logo_url'] = logo_elem.get('src', '')
                
                # Offre urgente
                urgent_elem = job.find('div', class_='urgent_flag')
                job_data['urgent'] = "Oui" if urgent_elem else "Non"
                
                # Secteur (à extraire du contexte ou des filtres si possible)
                job_data['secteur'] = self.extract_sector_from_context(job)
                
                # Référence (peut être dans le titre ou à extraire séparément)
                job_data['reference'] = self.extract_reference(job_data.get('titre', ''))
                
                job_listings.append(job_data)
                
            except Exception as e:
                print(f"Erreur lors de l'extraction d'une offre: {e}")
                continue
        
        return job_listings

    def extract_sector_from_context(self, job_element):
        """Extrait le secteur d'activité à partir du contexte"""
        # Essayons de trouver le secteur dans le texte
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
            'stagiaire': 'Stage'
        }
        
        # Vérifier le titre et la description
        title = job_element.find('h3').text.lower() if job_element.find('h3') else ''
        desc = job_element.find('a', class_='description').text.lower() if job_element.find('a', class_='description') else ''
        
        text_to_check = title + ' ' + desc
        
        for keyword, sector in sector_keywords.items():
            if keyword in text_to_check:
                return sector
        
        return 'Non spécifié'

    def extract_reference(self, title):
        """Extrait la référence de l'offre depuis le titre"""
        import re
        # Cherche les motifs de référence courants
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

    def scrape_page(self, page_url):
        """Scrape une page d'offres d'emploi"""
        try:
            print(f"Scraping de la page : {page_url}")
            response = self.session.get(page_url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            # Extraire les offres
            jobs = self.extract_job_details_from_html(response.text)
            
            print(f"✅ {len(jobs)} offres d'emploi trouvées")
            return jobs
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur de connexion: {e}")
            return []
        except Exception as e:
            print(f"Erreur: {e}")
            return []

    def scrape_multiple_pages(self, num_pages=5):
        """Scrape plusieurs pages d'offres"""
        all_jobs = []
        
        for page in range(1, num_pages + 1):
            if page == 1:
                url = f"{self.base_url}/emploi/liste"
            else:
                url = f"{self.base_url}/emploi/liste/page/{page}"
            
            print(f"\n📄 Traitement de la page {page}...")
            jobs = self.scrape_page(url)
            all_jobs.extend(jobs)
            
            # Pause entre les requêtes pour respecter le serveur
            if page < num_pages:
                time.sleep(1)
        
        return all_jobs

    def get_detailed_job_info(self, job_url):
        """Récupère les détails complets d'une offre spécifique"""
        try:
            print(f"\n🔍 Extraction des détails depuis: {job_url}")
            response = self.session.get(job_url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_details = {}
            
            # Titre complet
            title = soup.find('h1')
            if title:
                job_details['titre_complet'] = title.text.strip()
            
            # Entreprise (chercher dans différents endroits)
            company_selectors = [
                'div.company-info h2',
                'div.entreprise-name',
                'h2.entreprise',
                'div.fiche_annonce h2'
            ]
            
            company = None
            for selector in company_selectors:
                company = soup.select_one(selector)
                if company:
                    break
            
            if company:
                job_details['entreprise_complete'] = company.text.strip()
            
            # Localisation
            location_selectors = [
                'span.location',
                'div.localisation',
                'p.adresse'
            ]
            
            location = None
            for selector in location_selectors:
                location = soup.select_one(selector)
                if location:
                    break
            
            if location:
                job_details['localisation'] = location.text.strip()
            
            # Description complète
            desc_selectors = [
                'div.job-description',
                'div.description-annonce',
                'div.contenu-annonce',
                'article.contenu'
            ]
            
            description = None
            for selector in desc_selectors:
                description = soup.select_one(selector)
                if description:
                    break
            
            if description:
                job_details['description_complete'] = description.get_text(strip=True, separator='\n')
            
            # Compétences requises
            skills = soup.find_all(['li', 'span'], class_=['competence', 'skill', 'qualification'])
            if skills:
                job_details['competences'] = [skill.text.strip() for skill in skills]
            
            # Date de publication
            date_pub = soup.find('span', class_='date-publication') or soup.find('time')
            if date_pub:
                job_details['date_publication_detailed'] = date_pub.text.strip()
            
            # Salaire (si disponible)
            salary = soup.find('span', class_='salaire') or soup.find('strong', text='Salaire')
            if salary:
                job_details['salaire'] = salary.text.strip()
            
            return job_details
            
        except Exception as e:
            print(f"Erreur lors de l'extraction des détails: {e}")
            return {}

    def save_to_csv(self, jobs, filename=None):
        """Sauvegarde les offres dans un fichier CSV"""
        if not jobs:
            print("Aucune donnée à sauvegarder")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"offres_portaljob_{timestamp}.csv"
        
        # Définir les champs à exporter (sans logo_url pour éviter l'erreur)
        fieldnames = ['titre', 'entreprise', 'contrat', 'date_publication', 
                     'date_limite', 'urgent', 'lien', 'description', 
                     'secteur', 'reference']
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                # Filtrer les champs pour n'inclure que ceux dans fieldnames
                for job in jobs:
                    filtered_job = {k: v for k, v in job.items() if k in fieldnames}
                    writer.writerow(filtered_job)
            
            print(f"💾 {len(jobs)} offres sauvegardées dans: {filename}")
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde CSV: {e}")

    def save_to_json(self, jobs, filename=None):
        """Sauvegarde les offres dans un fichier JSON"""
        if not jobs:
            print("Aucune donnée à sauvegarder")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"offres_portaljob_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(jobs, jsonfile, ensure_ascii=False, indent=2)
            
            print(f"💾 {len(jobs)} offres sauvegardées dans: {filename}")
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde JSON: {e}")

    def display_jobs(self, jobs, limit=None):
        """Affiche les offres d'emploi"""
        if not jobs:
            print("Aucune offre à afficher")
            return
        
        display_count = limit if limit else len(jobs)
        
        for i, job in enumerate(jobs[:display_count], 1):
            print(f"\n{'='*60}")
            print(f"OFFRE {i}:")
            print(f"{'='*60}")
            print(f"Titre: {job.get('titre', 'N/A')}")
            print(f"Entreprise: {job.get('entreprise', 'N/A')}")
            print(f"Contrat: {job.get('contrat', 'N/A')}")
            print(f"Date publication: {job.get('date_publication', 'N/A')}")
            print(f"Date limite: {job.get('date_limite', 'Non spécifiée')}")
            print(f"Urgent: {job.get('urgent', 'Non')}")
            print(f"Secteur: {job.get('secteur', 'N/A')}")
            print(f"Référence: {job.get('reference', 'N/A')}")
            print(f"Lien: {job.get('lien', 'N/A')}")
            print(f"Description: {job.get('description', 'N/A')[:200]}...")

def main():
    """Fonction principale"""
    print("""
    ╔══════════════════════════════════════════════════╗
    ║   PORTALJOB MADAGASCAR SCRAPER                  ║
    ║   Extraction des offres d'emploi                 ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    scraper = PortalJobScraper()
    
    while True:
        print("\nOptions disponibles:")
        print("1. Scraper la première page")
        print("2. Scraper plusieurs pages")
        print("3. Extraire les détails d'une offre spécifique")
        print("4. Tester avec une page locale (HTML file)")
        print("5. Quitter")
        
        choice = input("\nVotre choix (1-5): ").strip()
        
        if choice == "1":
            # Scraper seulement la première page
            url = f"{scraper.base_url}/emploi/liste"
            jobs = scraper.scrape_page(url)
            scraper.display_jobs(jobs, limit=10)
            
            save = input("\nVoulez-vous sauvegarder les résultats ? (o/n): ").strip().lower()
            if save == 'o':
                format_choice = input("Format (csv/json/both): ").strip().lower()
                if format_choice in ['csv', 'both']:
                    scraper.save_to_csv(jobs)
                if format_choice in ['json', 'both']:
                    scraper.save_to_json(jobs)
        
        elif choice == "2":
            # Scraper plusieurs pages
            try:
                num_pages = int(input("Nombre de pages à scraper (1-20): ").strip() or 3)
                num_pages = max(1, min(num_pages, 20))  # Limiter à 20 pages max
                
                jobs = scraper.scrape_multiple_pages(num_pages)
                
                if jobs:
                    print(f"\n✅ Total: {len(jobs)} offres extraites")
                    scraper.display_jobs(jobs, limit=5)
                    
                    save = input("\nVoulez-vous sauvegarder les résultats ? (o/n): ").strip().lower()
                    if save == 'o':
                        format_choice = input("Format (csv/json/both): ").strip().lower()
                        if format_choice in ['csv', 'both']:
                            scraper.save_to_csv(jobs)
                        if format_choice in ['json', 'both']:
                            scraper.save_to_json(jobs)
                else:
                    print("❌ Aucune offre trouvée")
                    
            except ValueError:
                print("❌ Veuillez entrer un nombre valide")
        
        elif choice == "3":
            # Extraire les détails d'une offre spécifique
            job_url = input("Entrez l'URL complète de l'offre: ").strip()
            if not job_url:
                print("❌ URL invalide")
                continue
            
            details = scraper.get_detailed_job_info(job_url)
            
            if details:
                print("\n📋 DÉTAILS COMPLETS DE L'OFFRE:")
                print("=" * 50)
                for key, value in details.items():
                    if isinstance(value, list):
                        print(f"{key.replace('_', ' ').title()}:")
                        for item in value:
                            print(f"  • {item}")
                    else:
                        print(f"{key.replace('_', ' ').title()}: {value}")
            else:
                print("❌ Impossible d'extraire les détails")
        
        elif choice == "4":
            # Tester avec un fichier HTML local
            html_file = input("Chemin du fichier HTML: ").strip()
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                jobs = scraper.extract_job_details_from_html(html_content)
                print(f"\n✅ {len(jobs)} offres extraites du fichier")
                scraper.display_jobs(jobs, limit=5)
                
            except FileNotFoundError:
                print("❌ Fichier non trouvé")
            except Exception as e:
                print(f"❌ Erreur: {e}")
        
        elif choice == "5":
            print("\n✨ Au revoir!")
            break
        
        else:
            print("❌ Option invalide. Veuillez réessayer.")

if __name__ == "__main__":
    main()