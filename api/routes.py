"""
Définition des routes API - VERSION CORRIGÉE
"""

from flask import Blueprint, jsonify, request
from models.job_offer import JobOfferCollection
from scrapers.data_processor import DataProcessor
from models.risk_analyzer import RiskAnalyzer
import config

# Initialisation
bp = Blueprint('api', __name__)
data_processor = DataProcessor(config.DATA_DIR)
risk_analyzer = RiskAnalyzer()

# Charger les données au démarrage
offers_collection = data_processor.load_offers()

# Dictionnaire de synonymes pour la recherche
JOB_SYNONYMS = {
    'chauffeur': ['chauffeur', 'conducteur', 'driver', 'livreur', 'transporteur', 'mécanicien conducteur'],
    'mécanicien': ['mécanicien', 'mechanic', 'garagiste', 'mécanicien conducteur'],
    'conducteur': ['conducteur', 'chauffeur', 'driver', 'mécanicien conducteur'],
    'comptable': ['comptable', 'accountant', 'comptabilité'],
    'réceptionniste': ['réceptionniste', 'receptionist', 'accueil', 'standardiste'],
    'commercial': ['commercial', 'vendeur', 'sales', 'business', 'business developer'],
    'développeur': ['développeur', 'developer', 'dev', 'programmeur', 'ingénieur'],
    'coordinateur': ['coordinateur', 'coordinatrice', 'coordination'],
}

def search_offers_by_job(job_name, offers):
    """Recherche améliorée avec synonymes"""
    job_lower = job_name.lower()
    
    # Préparer les termes de recherche
    search_terms = [job_lower]
    if job_lower in JOB_SYNONYMS:
        search_terms.extend(JOB_SYNONYMS[job_lower])
    
    # Recherche dans tous les champs pertinents
    results = []
    for offer in offers:
        # Texte à analyser
        search_text = f"{offer.title} {offer.metier} {offer.secteur}".lower()
        
        # Vérifier chaque terme
        for term in search_terms:
            if term in search_text:
                results.append(offer)
                break  # Pas besoin de vérifier d'autres termes
    
    return results

@bp.route('/health', methods=['GET'])
def health_check():
    """Vérifier que l'API fonctionne"""
    return jsonify({
        "status": "healthy",
        "service": "Safe AI Job Analyzer",
        "offers_count": len(offers_collection.offers),
        "search_synonyms_active": True
    })

@bp.route('/offers', methods=['GET'])
def get_all_offers():
    """Récupérer toutes les offres"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    
    # Pagination simple
    start = (page - 1) * limit
    end = start + limit
    paginated_offers = offers_collection.offers[start:end]
    
    return jsonify({
        "page": page,
        "limit": limit,
        "total": len(offers_collection.offers),
        "offers": [offer.to_dict() for offer in paginated_offers]
    })

@bp.route('/offers/<job_name>', methods=['GET'])
def get_offers_by_job(job_name: str):
    """Récupérer les offres par métier - VERSION AMÉLIORÉE"""
    offers = offers_collection.offers
    
    # Recherche améliorée
    filtered = search_offers_by_job(job_name, offers)
    filtered_collection = JobOfferCollection(filtered)
    
    # Statistiques pour ce métier
    stats = filtered_collection.get_statistics() if filtered else {}
    
    return jsonify({
        "job": job_name,
        "search_method": "synonyms_enhanced",
        "synonyms_used": JOB_SYNONYMS.get(job_name.lower(), [job_name.lower()]),
        "count": len(filtered),
        "statistics": stats,
        "offers": [offer.to_dict() for offer in filtered]
    })

@bp.route('/risk-analysis', methods=['GET'])
def get_risk_analysis():
    """Analyse globale des risques"""
    analysis = data_processor.get_risk_analysis(offers_collection)
    
    # Ajouter l'exemple de démo
    demo_example = None
    for offer in offers_collection.offers:
        if offer.ia_risk_score >= 8:  # Offre à haut risque
            demo_example = {
                "title": offer.title,
                "metier": offer.metier,
                "score": offer.ia_risk_score,
                "level": offer.ia_risk_level,
                "secteur": offer.secteur,
                "location": offer.location
            }
            break
    
    analysis["demo_example"] = demo_example
    analysis["search_tip"] = "Utilisez 'chauffeur' pour trouver 'MÉCANICIEN CONDUCTEUR' (score 9/10)"
    
    return jsonify(analysis)

@bp.route('/recommendations/<current_job>', methods=['GET'])
def get_recommendations(current_job: str):
    """Obtenir des recommandations de transition - VERSION AMÉLIORÉE"""
    offers_data = [offer.to_dict() for offer in offers_collection.offers]
    
    # Rechercher le métier avec synonymes
    current_offers = search_offers_by_job(current_job, offers_collection.offers)
    
    if not current_offers:
        return jsonify({
            "error": f"Métier '{current_job}' non trouvé. Suggestions: {', '.join(JOB_SYNONYMS.get(current_job.lower(), []))}",
            "current_job": current_job,
            "recommendations": []
        }), 404
    
    # Calculer le risque moyen
    current_avg_risk = sum(o.ia_risk_score for o in current_offers) / len(current_offers)
    
    # Obtenir toutes les offres comme dictionnaires pour l'analyse
    all_offers_dict = [offer.to_dict() for offer in offers_collection.offers]
    
    # Obtenir les recommandations
    recommendations = risk_analyzer.analyze_job_transition(
        current_job, 
        all_offers_dict
    )
    
    return jsonify({
        "current_job": current_job,
        "current_avg_risk": round(current_avg_risk, 1),
        "current_offers_count": len(current_offers),
        "current_example": current_offers[0].to_dict() if current_offers else None,
        "recommendations": recommendations[:5]  # Top 5 seulement
    })

@bp.route('/search', methods=['GET'])
def search_offers():
    """Recherche avancée d'offres"""
    query = request.args.get('q', '')
    risk_level = request.args.get('risk', '')
    sector = request.args.get('sector', '')
    job_type = request.args.get('job', '')
    
    filtered = offers_collection
    
    # Recherche par texte avec synonymes
    if query:
        filtered_offers = []
        for offer in filtered.offers:
            search_text = f"{offer.title} {offer.metier} {offer.secteur} {offer.location}".lower()
            if query.lower() in search_text:
                filtered_offers.append(offer)
            else:
                # Vérifier les synonymes
                for synonym in JOB_SYNONYMS.get(query.lower(), []):
                    if synonym in search_text:
                        filtered_offers.append(offer)
                        break
        
        filtered = JobOfferCollection(filtered_offers)
    
    # Filtres additionnels
    if risk_level:
        filtered = filtered.filter_by_risk(risk_level)
    
    if sector:
        filtered = filtered.filter_by_sector(sector)
    
    if job_type:
        filtered_offers = search_offers_by_job(job_type, filtered.offers)
        filtered = JobOfferCollection(filtered_offers)
    
    return jsonify({
        "query": query,
        "filters": {
            "risk": risk_level,
            "sector": sector,
            "job": job_type
        },
        "count": len(filtered.offers),
        "offers": [offer.to_dict() for offer in filtered.offers[:20]]
    })

@bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Statistiques générales"""
    stats = offers_collection.get_statistics()
    
    # Compter par type de contrat
    contracts = {}
    for offer in offers_collection.offers:
        contracts[offer.contrat] = contracts.get(offer.contrat, 0) + 1
    
    # Compter par localisation
    locations = {}
    for offer in offers_collection.offers:
        locations[offer.location] = locations.get(offer.location, 0) + 1
    
    # Trouver les 3 métiers les plus à risque
    high_risk_jobs = []
    for offer in offers_collection.offers:
        if offer.ia_risk_score >= 7:
            high_risk_jobs.append({
                "title": offer.title,
                "metier": offer.metier,
                "score": offer.ia_risk_score,
                "level": offer.ia_risk_level
            })
    
    high_risk_jobs.sort(key=lambda x: x['score'], reverse=True)
    
    return jsonify({
        "overall": stats,
        "by_contract": contracts,
        "by_location": locations,
        "high_risk_jobs": high_risk_jobs[:3],
        "search_tips": {
            "chauffeur": "Trouve 'MÉCANICIEN CONDUCTEUR' (score 9/10)",
            "conducteur": "Même que chauffeur",
            "mécanicien": "Trouve les offres de mécanique"
        }
    })

@bp.route('/demo', methods=['GET'])
def get_demo_example():
    """Endpoint spécial pour la démo du hackathon"""
    # Trouver l'offre parfaite pour la démo
    demo_offer = None
    for offer in offers_collection.offers:
        if offer.ia_risk_score >= 8:
            demo_offer = offer
            break
    
    if not demo_offer:
        # Fallback à la première offre à risque moyen
        for offer in offers_collection.offers:
            if offer.ia_risk_score >= 5:
                demo_offer = offer
                break
    
    if not demo_offer and offers_collection.offers:
        demo_offer = offers_collection.offers[0]
    
    # Trouver des recommandations pour cette offre
    recommendations = []
    if demo_offer:
        offers_data = [offer.to_dict() for offer in offers_collection.offers]
        recommendations = risk_analyzer.analyze_job_transition(
            demo_offer.metier, 
            offers_data
        )[:3]
    
    return jsonify({
        "demo_title": "Exemple concret pour le hackathon",
        "problem_job": demo_offer.to_dict() if demo_offer else None,
        "recommendations": recommendations,
        "message": "Ceci montre comment notre solution identifie les métiers à risque et propose des alternatives"
    })