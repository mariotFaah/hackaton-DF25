#!/usr/bin/env python3
"""
Script simplifié pour importer les données JSON dans la base
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import SessionLocal, JobOffer
import json
from datetime import datetime
from sqlalchemy import func

def import_and_show():
    """Importer les données et afficher les statistiques"""
    print("📂 IMPORTATION DES DONNÉES JSON DANS MySQL")
    print("=" * 50)
    
    # Importer les données JSON existantes
    import_json_data()
    
    # Afficher les statistiques
    show_statistics()
    
    print("\n✅ Base de données peuplée avec succès!")

def import_json_data():
    """Importer les données des fichiers JSON dans MySQL"""
    db = SessionLocal()
    
    json_files = [
        "data/offres_cdd.json",
        "data/offres_emploi.json",
        "data/offres_toutes.json"
    ]
    
    imported_count = 0
    skipped_count = 0
    
    for json_file in json_files:
        if not os.path.exists(json_file):
            print(f"   ⚠  Fichier non trouvé: {json_file}")
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Format des fichiers
                if isinstance(data, dict) and 'offers' in data:
                    offers_data = data['offers']
                elif isinstance(data, list):
                    offers_data = data
                else:
                    print(f"   ⚠  Format invalide dans {json_file}")
                    continue
                
                print(f"   📖 Lecture de {json_file}: {len(offers_data)} offres")
                
                for i, offer_data in enumerate(offers_data, 1):
                    link = offer_data.get('link', '')
                    if not link:
                        skipped_count += 1
                        continue
                    
                    # Vérifier si l'offre existe déjà
                    existing = db.query(JobOffer.id).filter(
                        JobOffer.link == link
                    ).first()
                    
                    if not existing:
                        # Créer une nouvelle offre
                        try:
                            job_offer = JobOffer(
                                title=offer_data.get('title', 'Non spécifié')[:500],
                                link=link[:500],
                                company=offer_data.get('company', 'Non spécifié')[:200],
                                date_posted=str(offer_data.get('date', ''))[:100],
                                contract_type=offer_data.get('contrat', 'Non spécifié')[:100],
                                sector=offer_data.get('secteur', 'Non spécifié')[:200],
                                job_title=offer_data.get('metier', 'Non spécifié')[:200],
                                location=offer_data.get('location', 'Non spécifié')[:200],
                                description=offer_data.get('description', '')[:1000],
                                ia_risk_score=float(offer_data.get('ia_risk_score', 5.0)),
                                ia_risk_level=offer_data.get('ia_risk_level', 'Moyen')[:50],
                                suggestions=', '.join(offer_data.get('suggestions', []))[:1000],
                                scraped_at=datetime.utcnow(),
                                is_active=True
                            )
                            db.add(job_offer)
                            imported_count += 1
                            
                            # Commit périodiquement pour éviter les transactions trop longues
                            if imported_count % 10 == 0:
                                db.commit()
                                print(f"      → {imported_count} offres importées...")
                                
                        except Exception as e:
                            print(f"      ❌ Erreur création offre {i}: {e}")
                            skipped_count += 1
                    else:
                        skipped_count += 1  # Offre déjà existante
            
            db.commit()
            print(f"   ✅ {json_file}: import terminé")
            
        except Exception as e:
            print(f"❌ Erreur avec {json_file}: {e}")
            db.rollback()
            import traceback
            traceback.print_exc()
    
    db.close()
    print(f"\n📊 RÉSULTAT FINAL:")
    print(f"   → {imported_count} offres importées")
    print(f"   → {skipped_count} offres ignorées (doublons ou invalides)")

def show_statistics():
    """Afficher les statistiques de la base"""
    db = SessionLocal()
    
    try:
        total = db.query(func.count(JobOffer.id)).scalar() or 0
        
        print(f"\n📊 STATISTIQUES DE LA BASE:")
        print(f"   • Total offres: {total}")
        
        if total > 0:
            # Distribution des risques
            risk_levels = ['Élevé', 'Moyen', 'Faible']
            print(f"\n   📈 DISTRIBUTION DES RISQUES:")
            for level in risk_levels:
                count = db.query(func.count(JobOffer.id)).filter(
                    JobOffer.ia_risk_level == level
                ).scalar() or 0
                percentage = (count / total * 100) if total > 0 else 0
                print(f"     • {level}: {count} offres ({percentage:.1f}%)")
            
            # Top métiers
            top_jobs = db.query(
                JobOffer.job_title,
                func.count(JobOffer.id).label('count')
            ).filter(
                JobOffer.job_title != '',
                JobOffer.job_title != 'Non spécifié'
            ).group_by(
                JobOffer.job_title
            ).order_by(
                func.count(JobOffer.id).desc()
            ).limit(5).all()
            
            if top_jobs:
                print(f"\n   🏆 TOP 5 MÉTIERS:")
                for job, count in top_jobs:
                    print(f"     • {job}: {count} offres")
            
            # Top secteurs
            top_sectors = db.query(
                JobOffer.sector,
                func.count(JobOffer.id).label('count')
            ).filter(
                JobOffer.sector != '',
                JobOffer.sector != 'Non spécifié'
            ).group_by(
                JobOffer.sector
            ).order_by(
                func.count(JobOffer.id).desc()
            ).limit(5).all()
            
            if top_sectors:
                print(f"\n   🏢 TOP 5 SECTEURS:")
                for sector, count in top_sectors:
                    print(f"     • {sector}: {count} offres")
                    
            # Exemple d'offres
            print(f"\n   📝 EXEMPLES D'OFFRES:")
            sample_offers = db.query(JobOffer).limit(3).all()
            for i, offer in enumerate(sample_offers, 1):
                print(f"     {i}. {offer.title[:40]}...")
                print(f"        Métier: {offer.job_title}")
                print(f"        Risque: {offer.ia_risk_score}/10 ({offer.ia_risk_level})")
                print()
                
        else:
            print("   ⚠  Base de données vide - Essayez le scraping manuel")
            
    except Exception as e:
        print(f"❌ Erreur statistiques: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def main():
    print("🗄️  IMPORTATION DE DONNÉES DANS MySQL")
    print("=" * 50)
    print("ℹ️  Les tables existent déjà (créées par repair_database.py)")
    print("ℹ️  Importation des fichiers JSON...")
    
    import_and_show()
    
    print("\n🎯 PROCHAINES ÉTAPES:")
    print("1. Démarrer l'API: python3 run.py")
    print("2. Tester: curl http://localhost:5000/api/health")
    print("3. Scraper plus de données: python3 scrapers/run_scraper.py")

if __name__ == "__main__":
    main()