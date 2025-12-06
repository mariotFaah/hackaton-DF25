"""
Serveur API Flask principal
"""

from flask import Flask
from flask_cors import CORS
import config
from api.routes import bp as api_bp

def create_app():
    """Créer et configurer l'application Flask"""
    app = Flask(__name__)
    
    # Configuration CORS
    CORS(app, origins=config.API_CONFIG["cors_origins"])
    
    # Enregistrer les blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Route racine
    @app.route('/')
    def index():
        return {
            "service": "Safe AI Job Analyzer API",
            "version": "1.0.0",
            "endpoints": {
                "/api/health": "Vérifier l'état du service",
                "/api/offers": "Toutes les offres d'emploi",
                "/api/offers/<job>": "Offres par métier",
                "/api/risk-analysis": "Analyse des risques IA",
                "/api/recommendations/<job>": "Recommandations de transition",
                "/api/search": "Recherche d'offres",
                "/api/statistics": "Statistiques générales"
            }
        }
    
    # Gestion des erreurs
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Endpoint non trouvé"}, 404
    
    @app.errorhandler(500)
    def server_error(error):
        return {"error": "Erreur interne du serveur"}, 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host=config.API_CONFIG["host"],
        port=config.API_CONFIG["port"],
        debug=config.API_CONFIG["debug"]
    )