"""
Point d'entrée de l'application
"""

from api.server import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("🤖 SAFE AI HACKATHON - BACKEND API")
    print("=" * 60)
    print(f"API disponible sur: http://localhost:5000")
    print(f"Documentation: http://localhost:5000/")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)