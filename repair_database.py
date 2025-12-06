#!/usr/bin/env python3
"""
Script pour réparer complètement la base de données
"""

import sys
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def repair_database():
    """Réparer complètement la base de données"""
    print("🔧 RÉPARATION COMPLÈTE DE LA BASE DE DONNÉES")
    print("=" * 50)
    
    # Obtenir l'URL de la base de données
    db_url = os.getenv('DATABASE_URL', 'mysql+pymysql://admin:mot_de_passe@localhost/safe_ai_hackathon')
    
    # Extraire les informations de connexion
    db_url = db_url.replace('mysql+pymysql://', '')
    credentials, host_db = db_url.split('@', 1)
    user, password = credentials.split(':', 1)
    host = host_db.split('/')[0]
    database = host_db.split('/')[1] if '/' in host_db else 'safe_ai_hackathon'
    
    print(f"📊 Connexion à: {user}@{host}/{database}")
    
    # Connexion directe avec pymysql
    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # 1. Supprimer la base de données si elle existe
            print("\n1. Nettoyage de la base existante...")
            cursor.execute(f"DROP DATABASE IF EXISTS {database}")
            print(f"   → Base {database} supprimée")
            
            # 2. Créer une nouvelle base
            print("\n2. Création d'une nouvelle base...")
            cursor.execute(f"CREATE DATABASE {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"   → Base {database} créée")
            
            # 3. Sélectionner la base
            cursor.execute(f"USE {database}")
            
            # 4. Créer la table job_offers avec toutes les colonnes
            print("\n3. Création de la table job_offers...")
            cursor.execute("""
                CREATE TABLE job_offers (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    title VARCHAR(500) NOT NULL,
                    link VARCHAR(500) NOT NULL UNIQUE,
                    company VARCHAR(200),
                    date_posted VARCHAR(100),
                    contract_type VARCHAR(100),
                    sector VARCHAR(200),
                    job_title VARCHAR(200),
                    location VARCHAR(200),
                    description TEXT,
                    ia_risk_score FLOAT,
                    ia_risk_level VARCHAR(50),
                    suggestions TEXT,
                    scraped_at DATETIME,
                    is_active BOOLEAN DEFAULT TRUE,
                    INDEX idx_risk_level (ia_risk_level),
                    INDEX idx_job_title (job_title),
                    INDEX idx_location (location),
                    INDEX idx_sector (sector),
                    INDEX idx_scraped_at (scraped_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("   → Table job_offers créée avec toutes les colonnes")
            
            # 5. Créer la table job_recommendations
            print("\n4. Création de la table job_recommendations...")
            cursor.execute("""
                CREATE TABLE job_recommendations (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    original_job_id INT,
                    recommended_job_id INT,
                    score_difference FLOAT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (original_job_id) REFERENCES job_offers(id) ON DELETE CASCADE,
                    FOREIGN KEY (recommended_job_id) REFERENCES job_offers(id) ON DELETE CASCADE,
                    INDEX idx_original_job (original_job_id),
                    INDEX idx_recommended_job (recommended_job_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("   → Table job_recommendations créée")
            
            # 6. Créer la table statistics
            print("\n5. Création de la table statistics...")
            cursor.execute("""
                CREATE TABLE statistics (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    job_id INT,
                    analysis_type VARCHAR(100),
                    data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES job_offers(id) ON DELETE CASCADE,
                    INDEX idx_job (job_id),
                    INDEX idx_analysis_type (analysis_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("   → Table statistics créée")
            
        connection.commit()
        
        print("\n" + "=" * 50)
        print("✅ BASE DE DONNÉES RÉPARÉE AVEC SUCCÈS!")
        print("=" * 50)
        print("\n📊 Structure créée:")
        print("   • job_offers (table principale)")
        print("   • job_recommendations (avec FK)")
        print("   • statistics (avec FK)")
        print(f"\n🔗 Prête à être utilisée sur: {db_url}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la réparation: {e}")
        connection.rollback()
        raise
    finally:
        connection.close()

def verify_structure():
    """Vérifier la structure de la base"""
    print("\n🔍 VÉRIFICATION DE LA STRUCTURE...")
    
    db_url = os.getenv('DATABASE_URL', 'mysql+pymysql://admin:mot_de_passe@localhost/safe_ai_hackathon')
    db_url = db_url.replace('mysql+pymysql://', '')
    credentials, host_db = db_url.split('@', 1)
    user, password = credentials.split(':', 1)
    host = host_db.split('/')[0]
    database = host_db.split('/')[1] if '/' in host_db else 'safe_ai_hackathon'
    
    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # Vérifier les tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"📊 Tables trouvées ({len(tables)}):")
            for table in tables:
                print(f"   • {table[0]}")
            
            # Vérifier les colonnes de job_offers
            cursor.execute("DESCRIBE job_offers")
            columns = cursor.fetchall()
            print(f"\n📋 Colonnes de job_offers ({len(columns)}):")
            for col in columns:
                print(f"   • {col[0]:20} {col[1]:20} {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
                
    finally:
        connection.close()

def main():
    print("🔧 SCRIPT DE RÉPARATION DE BASE DE DONNÉES")
    print("=" * 50)
    
    try:
        # Réparer la base
        repair_database()
        
        # Vérifier
        verify_structure()
        
        print("\n🎯 PROCHAINES ÉTAPES:")
        print("1. Exécuter python3 init_database.py pour peupler la base")
        print("2. Démarrer l'API: python3 run.py")
        print("3. Tester: curl http://localhost:5000/api/health")
        
    except Exception as e:
        print(f"\n❌ Échec de la réparation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()