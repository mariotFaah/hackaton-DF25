import requests
from bs4 import BeautifulSoup
import json
import csv
from datetime import datetime

def extract_job_details_from_html(html_content):
    """
    Extrait les détails des offres d'emploi depuis le HTML fourni
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Trouver tous les articles d'offres d'emploi
    job_articles = soup.find_all('article', class_='item_annonce')
    
    job_listings = []
    
    for job in job_articles:
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
            job_data['date_limite'] = date_lim_elem.text.strip()
        
        # Logo de l'entreprise
        logo_elem = job.find('img')
        if logo_elem:
            job_data['logo'] = logo_elem.get('src', '')
        
        # Offre urgente
        urgent_elem = job.find('div', class_='urgent_flag')
        job_data['urgent'] = "Oui" if urgent_elem else "Non"
        
        # Secteur (peut être extrait du lien)
        # Note: Le secteur n'est pas directement visible dans l'article, 
        # mais pourrait être déduit du contexte ou extrait séparément
        
        job_listings.append(job_data)
    
    return job_listings

def scrape_job_listings(url, save_to_csv=True):
    """
    Scrape la page des offres d'emploi et extrait les détails
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"Scraping de la page : {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        # Extraire les offres
        jobs = extract_job_details_from_html(response.text)
        
        print(f"\n✅ {len(jobs)} offres d'emploi trouvées")
        
        # Afficher les détails
        for i, job in enumerate(jobs, 1):
            print(f"\n{'='*60}")
            print(f"OFFRE {i}:")
            print(f"{'='*60}")
            print(f"Titre: {job.get('titre', 'N/A')}")
            print(f"Entreprise: {job.get('entreprise', 'N/A')}")
            print(f"Contrat: {job.get('contrat', 'N/A')}")
            print(f"Date publication: {job.get('date_publication', 'N/A')}")
            print(f"Date limite: {job.get('date_limite', 'Non spécifiée')}")
            print(f"Urgent: {job.get('urgent', 'Non')}")
            print(f"Lien: {job.get('lien', 'N/A')}")
            print(f"Description: {job.get('description', 'N/A')[:200]}...")
        
        # Sauvegarder en CSV si demandé
        if save_to_csv and jobs:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"offres_emploi_{timestamp}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['titre', 'entreprise', 'contrat', 'date_publication', 
                            'date_limite', 'urgent', 'lien', 'description']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(jobs)
            
            print(f"\n💾 Données sauvegardées dans: {filename}")
        
        return jobs
        
    except Exception as e:
        print(f"Erreur: {e}")
        return []

def scrape_multiple_pages(base_url, num_pages=3):
    """
    Scrape plusieurs pages d'offres d'emploi
    """
    all_jobs = []
    
    for page in range(1, num_pages + 1):
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}/page/{page}"
        
        print(f"\n📄 Traitement de la page {page}...")
        jobs = scrape_job_listings(url, save_to_csv=False)
        all_jobs.extend(jobs)
    
    # Sauvegarder toutes les offres
    if all_jobs:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"toutes_offres_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['titre', 'entreprise', 'contrat', 'date_publication', 
                        'date_limite', 'urgent', 'lien', 'description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_jobs)
        
        print(f"\n✅ {len(all_jobs)} offres au total sauvegardées dans: {filename}")
    
    return all_jobs

def get_detailed_job_info(job_url):
    """
    Récupère les détails complets d'une offre spécifique
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"\n🔍 Extraction des détails depuis: {job_url}")
        response = requests.get(job_url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Exemple d'extraction de détails (à adapter selon la structure réelle de la page détaillée)
        job_details = {}
        
        # Titre
        title = soup.find('h1')
        if title:
            job_details['titre_complet'] = title.text.strip()
        
        # Entreprise
        company = soup.find('div', class_='company_name')  # À adapter
        if not company:
            company = soup.find('h2')
        if company:
            job_details['entreprise_complete'] = company.text.strip()
        
        # Localisation
        location = soup.find('span', class_='location')  # À adapter
        if location:
            job_details['localisation'] = location.text.strip()
        
        # Description complète
        description = soup.find('div', class_='job_description')  # À adapter
        if description:
            job_details['description_complete'] = description.get_text(strip=True, separator='\n')
        
        # Compétences requises
        skills = soup.find_all('span', class_='skill')  # À adapter
        if skills:
            job_details['competences'] = [skill.text.strip() for skill in skills]
        
        # Contact/Référence
        reference = soup.find('span', class_='reference')  # À adapter
        if reference:
            job_details['reference'] = reference.text.strip()
        
        # Afficher les détails
        print("\n📋 DÉTAILS COMPLETS DE L'OFFRE:")
        for key, value in job_details.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        
        return job_details
        
    except Exception as e:
        print(f"Erreur lors de l'extraction des détails: {e}")
        return {}

# Script principal
if __name__ == "__main__":
    # URL de la page des offres d'emploi
    base_url = "https://www.portaljob-madagascar.com/emploi/liste"
    
    print("""
    ╔══════════════════════════════════════════════════╗
    ║   SCRAPER PORTALJOB MADAGASCAR                   ║
    ║   Extraction des offres d'emploi                 ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    # Choix de l'utilisateur
    print("Options disponibles:")
    print("1. Scraper la première page")
    print("2. Scraper plusieurs pages")
    print("3. Tester avec le HTML fourni")
    print("4. Extraire les détails d'une offre spécifique")
    
    choice = input("\nVotre choix (1-4): ").strip()
    
    if choice == "1":
        # Scraper seulement la première page
        jobs = scrape_job_listings(base_url, save_to_csv=True)
        
    elif choice == "2":
        # Scraper plusieurs pages
        num_pages = int(input("Nombre de pages à scraper (max 532): ").strip() or 3)
        jobs = scrape_multiple_pages(base_url, min(num_pages, 10))
        
    elif choice == "3":
        # Utiliser le HTML fourni dans votre question
        print("\n🎯 Utilisation du HTML fourni...")
        
        # Note: Vous devez avoir le HTML dans une variable ou un fichier
        # Pour cet exemple, je vais simuler avec un exemple
        sample_html = """<html>...votre HTML ici...</html>"""
        
        # Décommentez la ligne suivante et remplacez par votre vrai HTML
        # jobs = extract_job_details_from_html(sample_html)
        
        print("\nPour utiliser cette option, insérez votre HTML dans le script.")
        
    elif choice == "4":
        # Extraire les détails d'une offre spécifique
        job_url = input("Entrez l'URL complète de l'offre: ").strip()
        if job_url:
            details = get_detailed_job_info(job_url)
        else:
            # Exemple avec une URL du site
            sample_job_url = "https://www.portaljob-madagascar.com/emploi/view/kontiki-service55-chargee-de-campagne-emailing-marketing-f181098"
            details = get_detailed_job_info(sample_job_url)
    
    else:
        print("Option invalide. Scraping de la première page...")
        jobs = scrape_job_listings(base_url, save_to_csv=True)
    
    print("\n✨ Opération terminée!")