import requests
from bs4 import BeautifulSoup

# URL du site
url = "https://www.portaljob-madagascar.com/emploi/liste"

try:
    # Envoyer une requête GET
    response = requests.get(url)
    response.raise_for_status()  # Vérifier si la requête a réussi
    
    # Vérifier l'encodage
    response.encoding = response.apparent_encoding
    
    # Parser le contenu HTML avec BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Afficher le code HTML complet
    print(soup.prettify())
    
    # Optionnel : sauvegarder dans un fichier
    with open('code_source.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    print("\nCode source sauvegardé dans 'code_source.html'")
    
except requests.exceptions.RequestException as e:
    print(f"Erreur de connexion : {e}")
except Exception as e:
    print(f"Une erreur est survenue : {e}")