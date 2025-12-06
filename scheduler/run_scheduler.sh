#!/bin/bash
# run_scheduler.sh - Démarrer le scheduler

cd /home/fakilo/Bureau/DF25_EKIPAKO/safe-ai-hackathon/backend

echo "🚀 Démarrage du scheduler Safe AI..."
echo "Date: $(date)"
echo ""

# Activer l'environnement virtuel
source venv/bin/activate

# Démarrer le scheduler en mode test
python3 scheduler/update_scheduler.py