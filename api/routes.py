"""
Routes API utilisant MySQL
"""

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_, and_
from database.models import JobOffer, get_db
from datetime import datetime
import config

bp = Blueprint('api', __name__)

@bp.route('/health')
def health():
    """Vérifier santé API + DB"""
    try:
        db = next(get_db())
        offer_count = db.query(func.count(JobOffer.id)).scalar()
        
        return jsonify({
            "status": "healthy",
            "database": "MySQL connected",
            "offers_count": offer_count,
            "service": "Safe AI Job Analyzer API",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/offers')
def get_offers():
    """Récupérer toutes les offres avec pagination et filtres"""
    db = next(get_db())
    
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    offset = (page - 1) * limit
    
    # Requête de base
    query = db.query(JobOffer).filter(JobOffer.is_active == True)
    
    # Appliquer les filtres
    risk_level = request.args.get('risk')
    if risk_level:
        query = query.filter(JobOffer.ia_risk_level == risk_level)
    
    location = request.args.get('location')
    if location:
        query = query.filter(JobOffer.location.contains(location))
    
    sector = request.args.get('sector')
    if sector:
        query = query.filter(JobOffer.sector.contains(sector))
    
    # Compter le total avant pagination
    total = query.count()
    
    # Appliquer pagination et tri
    offers = query.order_by(desc(JobOffer.scraped_at)).offset(offset).limit(limit).all()
    
    return jsonify({
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
        "offers": [offer.to_dict() for offer in offers]
    })

@bp.route('/offers/<job_name>')
@bp.route('/offers/<job_name>')
def get_offers_by_job(job_name):
    """Rechercher par métier - version améliorée"""
    db = next(get_db())
    
    # Nettoyer le nom du métier
    job_name_clean = job_name.lower().strip()
    
    # Recherche étendue avec synonymes
    synonyms = {
        'chauffeur': ['conducteur', 'driver', 'livreur'],
        'mécanicien': ['mechanic', 'garagiste'],
        'caissier': ['cashier', 'encaissement'],
        'secrétaire': ['secretary', 'assistant'],
        'comptable': ['accountant', 'finance']
    }
    
    search_terms = [job_name_clean]
    if job_name_clean in synonyms:
        search_terms.extend(synonyms[job_name_clean])
    
    # Construire la requête
    query = db.query(JobOffer).filter(JobOffer.is_active == True)
    
    # Créer les conditions OR
    conditions = []
    for term in search_terms:
        conditions.append(JobOffer.title.contains(term))
        conditions.append(JobOffer.job_title.contains(term))
        conditions.append(JobOffer.description.contains(term))
    
    if conditions:
        query = query.filter(or_(*conditions))
    
    offers = query.all()
    
    return jsonify({
        "job": job_name,
        "search_terms_used": search_terms,
        "count": len(offers),
        "offers": [offer.to_dict() for offer in offers]
    })

@bp.route('/risk-analysis')
def risk_analysis():
    """Analyse des risques IA depuis MySQL"""
    db = next(get_db())
    
    # Statistiques globales
    total = db.query(func.count(JobOffer.id)).filter(JobOffer.is_active == True).scalar() or 0
    
    if total == 0:
        return jsonify({"error": "Aucune donnée disponible"}), 404
    
    # Distribution des risques
    risk_distribution = {}
    for level in ['Élevé', 'Moyen', 'Faible']:
        count = db.query(func.count(JobOffer.id)).filter(
            JobOffer.is_active == True,
            JobOffer.ia_risk_level == level
        ).scalar() or 0
        risk_distribution[level] = count
    
    # Score moyen
    avg_score_result = db.query(func.avg(JobOffer.ia_risk_score)).filter(
        JobOffer.is_active == True
    ).scalar()
    avg_score = float(avg_score_result) if avg_score_result else 0.0
    
    # Top secteurs
    top_sectors = db.query(
        JobOffer.sector,
        func.count(JobOffer.id).label('count')
    ).filter(
        JobOffer.is_active == True,
        JobOffer.sector != ''
    ).group_by(JobOffer.sector).order_by(desc('count')).limit(5).all()
    
    # Top métiers
    top_metiers = db.query(
        JobOffer.job_title,
        func.count(JobOffer.id).label('count')
    ).filter(
        JobOffer.is_active == True,
        JobOffer.job_title != ''
    ).group_by(JobOffer.job_title).order_by(desc('count')).limit(5).all()
    
    # Secteurs à haut risque
    high_risk_sectors = db.query(
        JobOffer.sector,
        func.count(JobOffer.id).label('count')
    ).filter(
        JobOffer.is_active == True,
        JobOffer.ia_risk_level == 'Élevé',
        JobOffer.sector != ''
    ).group_by(
        JobOffer.sector
    ).order_by(desc('count')).limit(5).all()
    
    # Calcul pourcentage haut risque
    high_risk_count = risk_distribution.get('Élevé', 0)
    high_risk_percentage = (high_risk_count / total * 100) if total > 0 else 0
    
    return jsonify({
        "total_offers": total,
        "risk_distribution": risk_distribution,
        "average_risk_score": round(avg_score, 2),
        "high_risk_percentage": round(high_risk_percentage, 1),
        "top_sectors": [{"secteur": sector, "count": count} for sector, count in top_sectors],
        "top_metiers": [{"metier": metier, "count": count} for metier, count in top_metiers],
        "top_high_risk_sectors": [{"secteur": sector, "count": count} for sector, count in high_risk_sectors]
    })

@bp.route('/recommendations/<current_job>')
def get_recommendations(current_job):
    """Obtenir des recommandations de reconversion depuis MySQL"""
    db = next(get_db())
    
    # Trouver les offres du métier actuel
    current_offers = db.query(JobOffer).filter(
        JobOffer.is_active == True
    ).filter(
        or_(
            JobOffer.title.contains(current_job),
            JobOffer.job_title.contains(current_job)
        )
    ).all()
    
    if not current_offers:
        return jsonify({
            "current_job": current_job,
            "message": "Métier non trouvé dans la base de données",
            "recommendations": []
        })
    
    # Calculer le risque moyen du métier actuel
    current_scores = [o.ia_risk_score for o in current_offers if o.ia_risk_score is not None]
    if not current_scores:
        current_avg_risk = 5.0
    else:
        current_avg_risk = sum(current_scores) / len(current_scores)
    
    # Trouver des métiers à moindre risque (groupés par métier)
    recommendations_data = db.query(
        JobOffer.job_title,
        JobOffer.sector,
        func.avg(JobOffer.ia_risk_score).label('avg_score'),
        func.count(JobOffer.id).label('offer_count')
    ).filter(
        JobOffer.is_active == True,
        JobOffer.job_title != '',
        JobOffer.job_title != current_job,
        ~JobOffer.job_title.contains(current_job)
    ).group_by(
        JobOffer.job_title, JobOffer.sector
    ).having(
        func.avg(JobOffer.ia_risk_score) < current_avg_risk
    ).order_by(
        func.avg(JobOffer.ia_risk_score)
    ).limit(10).all()
    
    recommendations = []
    for job_title, sector, avg_score, offer_count in recommendations_data:
        # Trouver une offre exemple pour ce métier
        example_offer = db.query(JobOffer).filter(
            JobOffer.job_title == job_title,
            JobOffer.is_active == True
        ).first()
        
        avg_score_float = float(avg_score) if avg_score else 5.0
        
        recommendations.append({
            "metier": job_title,
            "avg_risk_score": round(avg_score_float, 1),
            "current_job_risk": round(current_avg_risk, 1),
            "risk_difference": round(current_avg_risk - avg_score_float, 1),
            "example_offer": example_offer.title if example_offer else "",
            "secteur": sector if sector else "Non spécifié",
            "offer_count": offer_count,
            "suggestions": example_offer.suggestions.split(', ') if example_offer and example_offer.suggestions else []
        })
    
    # Trier par différence de risque (du plus grand au plus petit)
    recommendations.sort(key=lambda x: x['risk_difference'], reverse=True)
    
    return jsonify({
        "current_job": current_job,
        "current_avg_risk": round(current_avg_risk, 1),
        "total_current_offers": len(current_offers),
        "recommendations": recommendations
    })

@bp.route('/search')
def search_offers():
    """Recherche avancée"""
    db = next(get_db())
    
    query = request.args.get('q', '').lower()
    min_risk = request.args.get('min_risk', 0, type=float)
    max_risk = request.args.get('max_risk', 10, type=float)
    sort_by = request.args.get('sort', 'date')
    
    # Construire la requête
    search_query = db.query(JobOffer).filter(JobOffer.is_active == True)
    
    # Filtre par score de risque
    if min_risk > 0 or max_risk < 10:
        search_query = search_query.filter(
            and_(
                JobOffer.ia_risk_score >= min_risk,
                JobOffer.ia_risk_score <= max_risk
            )
        )
    
    # Filtre par recherche textuelle
    if query:
        search_query = search_query.filter(
            or_(
                JobOffer.title.contains(query),
                JobOffer.job_title.contains(query),
                JobOffer.sector.contains(query),
                JobOffer.company.contains(query),
                JobOffer.location.contains(query),
                JobOffer.description.contains(query)
            )
        )
    
    # Appliquer le tri
    if sort_by == 'risk':
        search_query = search_query.order_by(desc(JobOffer.ia_risk_score))
    elif sort_by == 'date':
        search_query = search_query.order_by(desc(JobOffer.scraped_at))
    else:
        search_query = search_query.order_by(desc(JobOffer.scraped_at))
    
    # Limiter les résultats
    offers = search_query.limit(50).all()
    
    return jsonify({
        "query": query,
        "min_risk": min_risk,
        "max_risk": max_risk,
        "sort": sort_by,
        "count": len(offers),
        "offers": [offer.to_dict() for offer in offers]
    })

@bp.route('/statistics')
def get_statistics():
    """Statistiques générales depuis MySQL"""
    db = next(get_db())
    
    # Total offres actives
    total = db.query(func.count(JobOffer.id)).filter(JobOffer.is_active == True).scalar() or 0
    
    if total == 0:
        return jsonify({"error": "Aucune donnée disponible"}), 404
    
    # Distribution des risques
    risk_distribution = {'Élevé': 0, 'Moyen': 0, 'Faible': 0}
    for level in risk_distribution.keys():
        count = db.query(func.count(JobOffer.id)).filter(
            JobOffer.is_active == True,
            JobOffer.ia_risk_level == level
        ).scalar() or 0
        risk_distribution[level] = count
    
    # Score moyen
    avg_score_result = db.query(func.avg(JobOffer.ia_risk_score)).filter(
        JobOffer.is_active == True
    ).scalar()
    avg_score = round(float(avg_score_result) if avg_score_result else 0.0, 2)
    
    # Top secteurs
    top_sectors = db.query(
        JobOffer.sector,
        func.count(JobOffer.id).label('count')
    ).filter(
        JobOffer.is_active == True,
        JobOffer.sector != ''
    ).group_by(JobOffer.sector).order_by(desc('count')).limit(5).all()
    
    # Top localisations
    top_locations = db.query(
        JobOffer.location,
        func.count(JobOffer.id).label('count')
    ).filter(
        JobOffer.is_active == True,
        JobOffer.location != ''
    ).group_by(JobOffer.location).order_by(desc('count')).limit(5).all()
    
    # Top entreprises
    top_companies = db.query(
        JobOffer.company,
        func.count(JobOffer.id).label('count')
    ).filter(
        JobOffer.is_active == True,
        JobOffer.company != ''
    ).group_by(JobOffer.company).order_by(desc('count')).limit(5).all()
    
    return jsonify({
        "total_offers": total,
        "risk_distribution": risk_distribution,
        "average_risk_score": avg_score,
        "top_sectors": [{"secteur": sector, "count": count} for sector, count in top_sectors],
        "top_locations": [{"location": location, "count": count} for location, count in top_locations],
        "top_companies": [{"company": company, "count": count} for company, count in top_companies],
        "timestamp": datetime.now().isoformat()
    })

@bp.route('/sectors')
def get_sectors():
    """Récupérer tous les secteurs disponibles"""
    db = next(get_db())
    
    sectors = db.query(
        JobOffer.sector
    ).filter(
        JobOffer.is_active == True,
        JobOffer.sector != ''
    ).distinct().all()
    
    return jsonify({
        "sectors": [sector[0] for sector in sectors if sector[0]]
    })

@bp.route('/locations')
def get_locations():
    """Récupérer toutes les localisations disponibles"""
    db = next(get_db())
    
    locations = db.query(
        JobOffer.location
    ).filter(
        JobOffer.is_active == True,
        JobOffer.location != ''
    ).distinct().all()
    
    return jsonify({
        "locations": [location[0] for location in locations if location[0]]
    })

@bp.route('/offers/<int:offer_id>')
def get_offer_by_id(offer_id):
    """Récupérer une offre spécifique par ID"""
    db = next(get_db())
    
    offer = db.query(JobOffer).filter(JobOffer.id == offer_id).first()
    
    if not offer:
        return jsonify({"error": "Offre non trouvée"}), 404
    
    return jsonify({
        "offer": offer.to_dict()
    })


@bp.route('/search-job/<job_name>')
def search_job_enhanced(job_name):
    """Recherche améliorée par métier avec synonymes"""
    db = next(get_db())
    
    # Dictionnaire de synonymes pour Madagascar
    synonyms_dict = {
        'chauffeur': ['conducteur', 'driver', 'livreur', 'coursier', 'transporteur'],
        'mécanicien': ['mechanic', 'garagiste', 'réparateur', 'technicien auto'],
        'caissier': ['cashier', 'encaissement', 'hôte de caisse'],
        'secrétaire': ['secretary', 'assistant', 'assistante', 'secrétariat'],
        'comptable': ['accountant', 'finance', 'gestionnaire comptable'],
        'infirmier': ['nurse', 'infirmière', 'soignant', 'paramédical'],
        'enseignant': ['teacher', 'professeur', 'formateur', 'éducateur'],
        'développeur': ['developer', 'programmeur', 'informaticien', 'software'],
        'manager': ['chef', 'directeur', 'superviseur', 'responsable'],
        'coordinateur': ['coordinator', 'chef de projet', 'gestionnaire']
    }
    
    job_lower = job_name.lower()
    all_search_terms = [job_lower]
    
    # Ajouter les synonymes
    if job_lower in synonyms_dict:
        all_search_terms.extend(synonyms_dict[job_lower])
    
    print(f"🔍 Recherche avec termes: {all_search_terms}")
    
    # Construire la requête
    conditions = []
    for term in all_search_terms:
        conditions.append(JobOffer.title.contains(term))
        conditions.append(JobOffer.job_title.contains(term))
        conditions.append(JobOffer.description.contains(term))
        conditions.append(JobOffer.sector.contains(term))
    
    query = db.query(JobOffer).filter(
        JobOffer.is_active == True
    ).filter(
        or_(*conditions) if conditions else True
    )
    
    offers = query.all()
    
    # Analyse des résultats
    if offers:
        risk_stats = {"Élevé": 0, "Moyen": 0, "Faible": 0}
        for offer in offers:
            level = offer.ia_risk_level
            if level in risk_stats:
                risk_stats[level] += 1
        
        avg_risk = sum(o.ia_risk_score for o in offers) / len(offers)
        
        return jsonify({
            "job": job_name,
            "search_terms_used": all_search_terms,
            "count": len(offers),
            "average_risk": round(avg_risk, 2),
            "risk_distribution": risk_stats,
            "high_risk_percentage": round((risk_stats['Élevé'] / len(offers)) * 100, 1),
            "offers": [offer.to_dict() for offer in offers]
        })
    else:
        return jsonify({
            "job": job_name,
            "search_terms_used": all_search_terms,
            "count": 0,
            "message": f"Aucune offre trouvée pour '{job_name}'. Essayez avec un synonyme.",
            "suggested_synonyms": synonyms_dict.get(job_lower, []),
            "offers": []
        })

@bp.route('/jobs-by-risk')
def jobs_by_risk():
    """Obtenir les listes de travail par niveau de risque avec suggestions"""
    db = next(get_db())
    
    risk_level = request.args.get('level', 'all')  # 'high', 'medium', 'low', 'all'
    
    # Mapper les niveaux
    level_map = {
        'high': 'Élevé',
        'medium': 'Moyen', 
        'low': 'Faible'
    }
    
    # Construire la requête
    query = db.query(
        JobOffer.job_title,
        JobOffer.ia_risk_level,
        func.count(JobOffer.id).label('count'),
        func.avg(JobOffer.ia_risk_score).label('avg_score'),
        func.min(JobOffer.ia_risk_score).label('min_score'),
        func.max(JobOffer.ia_risk_score).label('max_score'),
        func.group_concat(JobOffer.suggestions).label('all_suggestions')
    ).filter(
        JobOffer.is_active == True,
        JobOffer.job_title != '',
        JobOffer.ia_risk_level != ''
    )
    
    # Si un niveau spécifique est demandé
    if risk_level != 'all' and risk_level in level_map:
        french_level = level_map[risk_level]
        query = query.filter(JobOffer.ia_risk_level == french_level)
    
    # Exécuter la requête
    jobs_data = query.group_by(
        JobOffer.job_title, JobOffer.ia_risk_level
    ).order_by(
        desc('count')
    ).all()
    
    # Traiter les résultats
    processed_jobs = []
    for job_title, risk_level_fr, count, avg_score, min_score, max_score, all_suggestions in jobs_data:
        # Déterminer la clé anglaise
        risk_key = None
        for key, value in level_map.items():
            if value == risk_level_fr:
                risk_key = key
                break
        
        if risk_key is None:
            risk_key = 'medium'
        
        # Nettoyer les suggestions
        suggestions_list = []
        if all_suggestions:
            # Séparer par virgule, nettoyer et dédupliquer
            suggestions = [s.strip() for s in all_suggestions.split(',') if s.strip()]
            # Enlever les parenthèses incomplètes
            clean_suggestions = []
            for s in suggestions:
                if 'Excel' in s and 'outils de gestion)' in s:
                    # Corriger la suggestion coupée
                    clean_suggestions.append("Formation en compétences numériques (Excel, outils de gestion)")
                else:
                    clean_suggestions.append(s)
            suggestions_list = list(set(clean_suggestions))[:5]
        
        # Si pas de suggestions, utiliser des suggestions par défaut
        if not suggestions_list:
            if risk_level_fr == 'Élevé':
                suggestions_list = [
                    "Formation en compétences numériques (Excel, outils de gestion)",
                    "Reconversion vers la logistique ou la coordination",
                    "Développement de compétences en gestion de projet",
                    "Apprentissage des outils de relation client (CRM)"
                ]
            elif risk_level_fr == 'Moyen':
                suggestions_list = [
                    "Renforcement des compétences relationnelles",
                    "Apprentissage des outils digitaux de votre secteur",
                    "Spécialisation dans un créneau à forte valeur ajoutée"
                ]
            else:
                suggestions_list = [
                    "Continuer à se former dans votre domaine",
                    "Développer une expertise complémentaire",
                    "Renforcer vos compétences en leadership"
                ]
        
        # Trouver un exemple d'offre
        example_offer = db.query(JobOffer).filter(
            JobOffer.job_title == job_title,
            JobOffer.ia_risk_level == risk_level_fr,
            JobOffer.is_active == True
        ).first()
        
        job_info = {
            'job_title': job_title,
            'risk_level': risk_level_fr,
            'risk_level_en': risk_key,
            'count': count,
            'avg_risk_score': round(float(avg_score) if avg_score else 5.0, 1),
            'min_risk_score': round(float(min_score) if min_score else 5.0, 1),
            'max_risk_score': round(float(max_score) if max_score else 5.0, 1),
            'suggestions': suggestions_list,
            'example_title': example_offer.title if example_offer else "",
            'example_sector': example_offer.sector if example_offer else "",
            'example_company': example_offer.company if example_offer else ""
        }
        
        processed_jobs.append(job_info)
    
    # Organiser la réponse
    if risk_level == 'all':
        # Grouper par niveau de risque
        jobs_by_risk = {'high': [], 'medium': [], 'low': []}
        stats = {'high': {'total_jobs': 0, 'total_offers': 0, 'avg_risk_score': 0.0},
                'medium': {'total_jobs': 0, 'total_offers': 0, 'avg_risk_score': 0.0},
                'low': {'total_jobs': 0, 'total_offers': 0, 'avg_risk_score': 0.0}}
        
        for job in processed_jobs:
            risk_key = job['risk_level_en']
            jobs_by_risk[risk_key].append(job)
        
        # Calculer les statistiques
        for risk_key in ['high', 'medium', 'low']:
            jobs = jobs_by_risk[risk_key]
            if jobs:
                stats[risk_key] = {
                    'total_jobs': len(jobs),
                    'total_offers': sum(j['count'] for j in jobs),
                    'avg_risk_score': round(sum(j['avg_risk_score'] for j in jobs) / len(jobs), 1)
                }
        
        return jsonify({
            'requested_level': risk_level,
            'statistics': stats,
            'jobs_by_risk': jobs_by_risk,
            'timestamp': datetime.now().isoformat()
        })
    else:
        # Pour un niveau spécifique
        if processed_jobs:
            stats = {
                'total_jobs': len(processed_jobs),
                'total_offers': sum(j['count'] for j in processed_jobs),
                'avg_risk_score': round(sum(j['avg_risk_score'] for j in processed_jobs) / len(processed_jobs), 1)
            }
        else:
            stats = {
                'total_jobs': 0,
                'total_offers': 0,
                'avg_risk_score': 0.0
            }
        
        return jsonify({
            'requested_level': risk_level,
            'statistics': stats,
            'jobs': processed_jobs,  # Liste plate, pas d'objets vides
            'timestamp': datetime.now().isoformat()
        })


@bp.route('/jobs-by-risk-detailed')
def jobs_by_risk_detailed():
    """Liste détaillée des métiers par niveau de risque avec filtres"""
    db = next(get_db())
    
    # Récupérer les paramètres de filtre
    risk_level = request.args.get('level', 'all')  # high, medium, low, all
    min_offers = request.args.get('min_offers', 1, type=int)
    sector = request.args.get('sector', '')
    
    # Construire la requête de base
    query = db.query(
        JobOffer.job_title,
        JobOffer.ia_risk_level,
        JobOffer.sector,
        func.count(JobOffer.id).label('offer_count'),
        func.avg(JobOffer.ia_risk_score).label('avg_score'),
        func.group_concat(JobOffer.company.distinct()).label('companies'),
        func.group_concat(JobOffer.suggestions).label('all_suggestions'),
        func.min(JobOffer.scraped_at).label('first_seen'),
        func.max(JobOffer.scraped_at).label('last_seen')
    ).filter(
        JobOffer.is_active == True,
        JobOffer.job_title != '',
        JobOffer.ia_risk_level != ''
    )
    
    # Appliquer les filtres
    if risk_level != 'all':
        risk_map = {'high': 'Élevé', 'medium': 'Moyen', 'low': 'Faible'}
        if risk_level in risk_map:
            query = query.filter(JobOffer.ia_risk_level == risk_map[risk_level])
    
    if sector:
        query = query.filter(JobOffer.sector.contains(sector))
    
    # Exécuter la requête
    jobs_data = query.group_by(
        JobOffer.job_title, JobOffer.ia_risk_level, JobOffer.sector
    ).having(
        func.count(JobOffer.id) >= min_offers
    ).order_by(
        desc('offer_count')
    ).all()
    
    # Organiser les résultats
    risk_categories = {
        'Élevé': {'title': 'Risque Élevé', 'color': '#ef4444', 'jobs': []},
        'Moyen': {'title': 'Risque Moyen', 'color': '#f59e0b', 'jobs': []},
        'Faible': {'title': 'Risque Faible', 'color': '#10b981', 'jobs': []}
    }
    
    for job in jobs_data:
        job_title, risk_level_fr, job_sector, offer_count, avg_score, companies, all_suggestions, first_seen, last_seen = job
        
        # Traiter les suggestions
        suggestions_list = []
        if all_suggestions:
            # Séparer par virgules et nettoyer
            raw_suggestions = [s.strip() for s in all_suggestions.split(',') if s.strip()]
            # Garder les suggestions uniques
            unique_suggestions = []
            seen = set()
            for suggestion in raw_suggestions:
                if suggestion not in seen:
                    seen.add(suggestion)
                    unique_suggestions.append(suggestion)
            suggestions_list = unique_suggestions[:5]  # Limiter à 5
        
        # Liste des entreprises
        companies_list = []
        if companies:
            companies_list = list(set([c.strip() for c in companies.split(',') if c.strip()]))[:5]
        
        job_info = {
            'job_title': job_title,
            'sector': job_sector if job_sector else 'Non spécifié',
            'offer_count': offer_count,
            'avg_risk_score': round(float(avg_score) if avg_score else 5.0, 1),
            'companies': companies_list,
            'suggestions': suggestions_list if suggestions_list else [
                "Consultez un conseiller en orientation professionnelle",
                "Explorez les formations disponibles dans votre région",
                "Développez des compétences transversales"
            ],
            'first_seen': first_seen.isoformat() if first_seen else None,
            'last_seen': last_seen.isoformat() if last_seen else None,
            'time_range_days': (last_seen - first_seen).days if first_seen and last_seen else 0
        }
        
        if risk_level_fr in risk_categories:
            risk_categories[risk_level_fr]['jobs'].append(job_info)
    
    # Trier les jobs par nombre d'offres (décroissant)
    for category in risk_categories.values():
        category['jobs'].sort(key=lambda x: x['offer_count'], reverse=True)
    
    # Calculer les totaux
    totals = {
        'total_jobs': sum(len(cat['jobs']) for cat in risk_categories.values()),
        'total_offers': sum(sum(j['offer_count'] for j in cat['jobs']) for cat in risk_categories.values()),
        'by_risk_level': {
            level: {'jobs': len(cat['jobs']), 'offers': sum(j['offer_count'] for j in cat['jobs'])}
            for level, cat in risk_categories.items()
        }
    }
    
    return jsonify({
        'filters_applied': {
            'risk_level': risk_level,
            'min_offers': min_offers,
            'sector': sector
        },
        'totals': totals,
        'risk_categories': risk_categories,
        'timestamp': datetime.now().isoformat()
    })