📡 **URL de l'API :** http://localhost:5000
🔥 **Exemple parfait pour la démo :** "MECANICIEN CONDUCTEUR" (score IA 9/10 - RISQUE ÉLEVÉ)

📊 **Données disponibles :** 50 offres d'emploi réelles d'asako.mg

🚀 **ENDPOINTS DISPONIBLES :**

1. GET  /api/health           → Vérifier que l'API fonctionne
2. GET  /api/offers           → Toutes les offres (50)
3. GET  /api/offers/chauffeur → Offres pour chauffeurs/conducteurs
4. GET  /api/recommendations/chauffeur → Alternatives à moindre risque
5. GET  /api/risk-analysis    → Analyse complète des risques
6. GET  /api/search?q=chauffeur → Recherche avancée
7. GET  /api/demo             → Exemple parfait pour le pitch
8. GET  /api/statistics       → Statistiques globales

🎯 **POUR LA DÉMO :**
- Focus sur : "MECANICIEN CONDUCTEUR" (score 9/10)
- Recherche : "chauffeur" trouve automatiquement "conducteur"
- Recommandations : alternatives à risque plus faible

📦 **Structure des données (TypeScript) :**
interface JobOffer {
  title: string;
  link: string;
  company: string;
  date: string;
  contrat: string;
  secteur: string;
  metier: string;
  location: string;
  ia_risk_score: number;      // 1-10 (10 = risque élevé)
  ia_risk_level: "Faible" | "Moyen" | "Élevé";
}

⚠️ **IMPORTANT :**
- L'API tourne sur http://localhost:5000
- Installer axios : `npm install axios`
- Test rapide : `curl http://localhost:5000/api/health`

💡 **Idées pour le frontend :**
1. Page recherche : champ "Votre métier" → résultats
2. Page détail : risque IA + alternatives
3. Dashboard : statistiques globales
4. Page démo : focus sur "MECANICIEN CONDUCTEUR"

Le backend est stable et prêt. Tu peux commencer l'intégration immédiatement !

Bonne chance pour le hackathon! 🚀

[Ton nom]
📄 DOCUMENTATION TECHNIQUE DÉTAILLÉE :
Fichier : API_DOCUMENTATION.md

markdown
# Safe AI Hackathon - Documentation API Backend

## Base URL
`http://localhost:5000`

## Endpoints

### 1. Health Check
**GET `/api/health`**
```json
{
  "status": "healthy",
  "service": "Safe AI Job Analyzer",
  "offers_count": 50,
  "search_synonyms_active": true
}
```
### 2. Toutes les offres
**GET /api/offers**

```bash
json
{
  "page": 1,
  "limit": 50,
  "total": 50,
  "offers": [
    {
      "title": "MECANICIEN CONDUCTEUR",
      "metier": "Mécanicien",
      "ia_risk_score": 9,
      "ia_risk_level": "Élevé",
      "secteur": "Automobile",
      "location": "Nosy Be",
      "contrat": "CDD"
    }
  ]
}
```

### 3. Offres par métier
**GET /api/offers/chauffeur**

Recherche améliorée avec synonymes

"chauffeur" → trouve aussi "conducteur", "driver", "livreur"

### 4. Recommandations de transition
GET /api/recommendations/chauffeur

Pour un métier donné

Propose des alternatives à moindre risque

Retourne top 5 recommandations

### 5. Analyse des risques
GET /api/risk-analysis

Statistiques globales

Analyse par métier

Exemple de démo inclus

### 6. Recherche avancée
GET /api/search?q=chauffeur&risk=Élevé&sector=Automobile

Recherche texte + filtres

Filtres : risque, secteur, type de métier

### 7. Endpoint démo
GET /api/demo

Exemple parfait pour le pitch

"MECANICIEN CONDUCTEUR" (score 9/10)

Recommandations alternatives

### 8. Statistiques
GET /api/statistics

Par type de contrat

Par localisation

Métiers les plus à risque

Exemple de flux pour la démo
Recherche "chauffeur" → trouve "MECANICIEN CONDUCTEUR"

Analyse risque → score 9/10 (ÉLEVÉ)

Recommandations → alternatives à risque plus faible

Parcours formation → comment se reconvertir

Structure des données
typescript

```bash
interface JobOffer {
  title: string;           // "MECANICIEN CONDUCTEUR"
  link: string;            // URL asako.mg
  company: string;         // "madagascar-ground-handling"
  date: string;           // "Il y a 4 jours"
  contrat: string;        // "CDD", "CDI", "freelance", "stage"
  secteur: string;        // "Automobile"
  metier: string;         // "Mécanicien"
  location: string;       // "Nosy Be"
  ia_risk_score: number;  // 9 (1-10, 10 = très risqué)
  ia_risk_level: string;  // "Élevé", "Moyen", "Faible"
}

interface Recommendation {
  job: JobOffer;
  difference_risk: number;  // Réduction du risque
  reason: string;          // Pourquoi c'est mieux
}
```
### Points d'intégration frontend
Service API : axios.create({ baseURL: 'http://localhost:5000/api' })

Pages principales :

/ : Recherche + résultats

/dashboard : Statistiques

/demo : Exemple hackathon

Composants :

JobSearch : Champ recherche

RiskIndicator : Visualisation risque

Recommendations : Liste alternatives

Statistics : Graphiques

Tests rapides
```bash
# Vérifier API
curl http://localhost:5000/api/health

# Exemple démo
curl http://localhost:5000/api/demo

# Recherche chauffeur
curl http://localhost:5000/api/offers/chauffeur
```
Pour le hackathon
Pitch : "De chauffeur à coordinateur logistique - Notre IA vous montre le chemin !"

Démo :

Montrer "MECANICIEN CONDUCTEUR" (9/10)

Montrer alternatives proposées

Montrer parcours de transition

text

### **⚡ CODE D'EXEMPLE POUR LE FRONTEND :**

**Fichier : `frontend/src/services/api.js` (à envoyer aussi)**
```javascript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

export const apiService = {
  // Vérifier santé API
  checkHealth: () => api.get('/health'),
  
  // Toutes les offres
  getAllOffers: () => api.get('/offers'),
  
  // Offres par métier
  getOffersByJob: (job) => api.get(`/offers/${job}`),
  
  // Recommandations
  getRecommendations: (job) => api.get(`/recommendations/${job}`),
  
  // Analyse risques
  getRiskAnalysis: () => api.get('/risk-analysis'),
  
  // Endpoint démo
  getDemo: () => api.get('/demo'),
  
  // Statistiques
  getStatistics: () => api.get('/statistics'),
  
  // Recherche
  search: (query, filters = {}) => 
    api.get('/search', { params: { q: query, ...filters } }),
};
```
### NOUVEL ENDPOINT AJOUTÉ :
```bash
GET /api/jobs-by-risk
```
**Paramètres disponibles :**
?level=high → Métiers à haut risque uniquement

?level=medium → Métiers à risque moyen uniquement

?level=low → Métiers à faible risque uniquement

Pas de paramètre → Tous les métiers groupés par niveau

#### 📊 Exemples d'utilisation :
```javascript
// Exemple avec Axios
const apiService = {
  // Obtenir tous les métiers groupés par risque
  getJobsByRiskLevel: (level = 'all') => 
    axios.get(`/api/jobs-by-risk?level=${level}`),
  
  // Obtenir uniquement les métiers à haut risque
  getHighRiskJobs: () => 
    axios.get('/api/jobs-by-risk?level=high'),
  
  // Obtenir uniquement les métiers à faible risque
  getLowRiskJobs: () => 
    axios.get('/api/jobs-by-risk?level=low'),
}
```
🏗️ Structure de la réponse :
Pour GET /api/jobs-by-risk (tous les niveaux) :
```json
{
  "requested_level": "all",
  "statistics": {
    "high": {
      "total_jobs": 1,
      "total_offers": 1,
      "avg_risk_score": 9.0
    },
    "medium": {
      "total_jobs": 4, 
      "total_offers": 8,
      "avg_risk_score": 6.0
    },
    "low": {
      "total_jobs": 5,
      "total_offers": 7,
      "avg_risk_score": 3.1
    }
  },
  "jobs_by_risk": {
    "high": [
      {
        "job_title": "Mécanicien",
        "risk_level": "Élevé",
        "risk_level_en": "high",
        "count": 1,
        "avg_risk_score": 9.0,
        "suggestions": ["Formation en compétences...", "..."]
      }
    ],
    "medium": [...],
    "low": [...]
  }
}
```
#### Pour GET /api/jobs-by-risk?level=high :
```json
{
  "requested_level": "high",
  "statistics": {
    "total_jobs": 1,
    "total_offers": 1,
    "avg_risk_score": 9.0
  },
  "jobs": [
    {
      "job_title": "Mécanicien",
      "risk_level": "Élevé",
      "risk_level_en": "high",
      "count": 1,
      "avg_risk_score": 9.0,
      "suggestions": [
        "Formation en compétences numériques (Excel, outils de gestion)",
        "Reconversion vers la logistique ou la coordination",
        "Développement de compétences en gestion de projet",
        "Apprentissage des outils de relation client (CRM)"
      ],
      "example_title": "MECANICIEN CONDUCTEUR",
      "example_sector": "Automobile",
      "example_company": "Madagascar Ground Handling"
    }
  ]
}
```

🎯 POUR LE PITCH DE 5 MINUTES :
Scénario de démo :

text
1. "Jean est chauffeur à Madagascar" (00:00-01:00)
2. "Notre IA analyse son métier : risque 9/10" (01:00-02:00) 
3. "Nous proposons 3 alternatives à moindre risque" (02:00-03:00)
4. "Avec parcours de formation personnalisé" (03:00-04:00)
5. "Impact : protéger les emplois malgaches" (04:00-05:00)
Visuals pour la démo :

text
Écran 1 : Recherche "chauffeur" → "MECANICIEN CONDUCTEUR" 🔴
Écran 2 : Score IA 9/10 → "RISQUE ÉLEVÉ" ⚠️
Écran 3 : Alternatives → "Coordinateur logistique" 🟢 (score 1/10)
Écran 4 : Parcours formation → "3 mois de formation"
✅ RÉSUMÉ FINAL :
OUI, votre backend est PRÊT et vous pouvez dire au frontend :

✅ API stable sur http://localhost:5000

✅ Données réelles : 50 offres d'asako.mg

✅ Exemple parfait : "MECANICIEN CONDUCTEUR" (9/10)

✅ Endpoints complets : 8 endpoints documentés

✅ Recherche intelligente : synonymes activés

✅ Prêt pour l'intégration immédiate

