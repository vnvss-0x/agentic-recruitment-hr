<div align="center">

# 🤖 Assistant Intelligent de Recrutement RH

**Système multi-agent orchestré par LangGraph pour l'automatisation intelligente du recrutement**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.59-1C3C3C?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Gemini](https://img.shields.io/badge/Gemini_2.5--Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5.23-FF6F00?logo=databricks&logoColor=white)](https://www.trychroma.com)

[Architecture](#-architecture) · [Agents](#-les-5-agents) · [RAG](#-rag-agentique) · [HITL](#-human-in-the-loop-hitl) · [Installation](#-installation) · [API](#-api-reference) · [Démo](#-démonstration)

</div>

--- 


<div align="center">

## 📕 Rapport Complet du Projet

</div>

> ### 📄 **[`Agentic_AI_Project_Report.pdf`](Agentic_AI_Project_Report.pdf)**
>
> Le **rapport académique complet** (33 pages) accompagne ce dépôt.
<div align="center">
    <a href="Agentic_AI_Project_Report.pdf" style="background-color: #007BFF; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
        ⬇️ Télécharger le rapport (PDF) ⬇️
    </a>
</div>

---

## 📋 Table des matières

- [Présentation](#-présentation)
- [Architecture](#-architecture)
- [Les 5 Agents](#-les-5-agents)
- [RAG Agentique](#-rag-agentique)
- [Human-in-the-Loop (HITL)](#-human-in-the-loop-hitl)
- [Évaluation des Prompts](#-évaluation-des-prompts)
- [Stack Technique](#-stack-technique)
- [Structure du Projet](#-structure-du-projet)
- [Installation](#-installation)
- [API Reference](#-api-reference)
- [WebSocket — Streaming Temps Réel](#-websocket--streaming-temps-réel)
- [Démonstration](#-démonstration)
- [Tests](#-tests)
- [Perspectives](#-perspectives)

---

## 🎯 Présentation

L'**Assistant Intelligent de Recrutement RH** automatise l'intégralité du cycle de recrutement — de l'analyse de l'offre d'emploi à la génération du rapport final — tout en maintenant un **contrôle humain** sur les décisions critiques.

Le système repose sur **5 agents IA spécialisés**, orchestrés par un graphe d'état **LangGraph**, enrichis par une base de connaissances **RAG** (ChromaDB), et supervisés par **2 points de validation humaine** (HITL). Une interface web **React + FastAPI** avec communication **WebSocket temps réel** permet de piloter l'ensemble du pipeline.

### Pourquoi le recrutement ?

| Argument | Détail |
|----------|--------|
| **Volume de données** | Les entreprises reçoivent des centaines de CVs par offre, rendant l'automatisation indispensable |
| **Complexité décisionnelle** | La sélection nécessite d'analyser des dimensions multiples (compétences, soft skills, fit culturel) |
| **Enjeux humains** | Les décisions impactent des vies, justifiant la présence d'un humain dans la boucle |
| **Richesse documentaire** | CVs, fiches de poste, grilles d'évaluation → base idéale pour le RAG |

---

## 🏗 Architecture

### Orchestration hiérarchique avec LangGraph

Le système utilise un **StateGraph** LangGraph avec routage conditionnel. Contrairement à une chaîne séquentielle simple, cette architecture permet :

- Des **cycles et boucles** dans le flux (ex : relancer les entretiens)
- La **persistance d'état** entre les étapes via `RecruitmentState`
- Des **interruptions contrôlées** (`interrupt_before`) pour le HITL
- Un **routage conditionnel** basé sur l'état courant

### Flux du pipeline

```
┌─────────────┐     ┌──────────────┐     ┌──────────┐     ┌────────────────────┐
│  Agent 1    │────▸│   Agent 2    │────▸│  HITL 1  │────▸│     Agent 3        │
│ Analyse     │     │  Screening   │     │   (RH)   │     │  Questions         │
│ du Poste    │     │  & Scoring   │     │          │     │  d'Entretien       │
└─────────────┘     └──────────────┘     └────┬─────┘     └─────────┬──────────┘
                                              │                     │
                                    ┌─────────┘                     │
                                    │ réanalyse                     ▼
                                    ▼                     ┌────────────────────┐
                              Agent 2 (retry)             │     Agent 4        │
                                                          │  Analyse Réponses  │
                                                          └─────────┬──────────┘
                                                                    │
                                                                    ▼
┌─────────────┐     ┌──────────────┐                      ┌──────────────────┐
│  Agent 5    │◂────│   HITL 2     │◂─────────────────────│    Routage       │
│ Rapport     │hire │  (Manager)   │                      │  Conditionnel    │
│ Final       │     └──────┬───────┘                      └──────────────────┘
└─────────────┘            │
                           ├── additional_interview ──▸ Agent 3 (retry)
                           └── cancel ──▸ END
```

### Architecture web

```
┌────────────────────────┐         ┌─────────────────────────┐         ┌──────────────┐
│       Frontend         │         │        Backend           │         │   Vector DB  │
│  React + Vite          │ REST +  │   FastAPI + Python 3.11  │ Python  │   ChromaDB   │
│  Zustand + Tailwind    │◀═══════▸│   LangGraph              │◀═══════▸│  Embeddings  │
│  Framer Motion         │  WS     │   Gemini 2.5-Flash       │  API    │  Persistant  │
└────────────────────────┘         └─────────────────────────┘         └──────────────┘
```

---

## 🤖 Les 5 Agents

### Agent 1 — Analyse du Poste `job_analyzer.py`

| | |
|---|---|
| **Rôle** | Extraire les critères structurés du poste |
| **Entrée** | Offre d'emploi brute (texte) |
| **Sortie** | `JobProfile` structuré + enrichissement RAG |
| **LLM** | Gemini 2.5-Flash |

**Éléments extraits :** compétences techniques avec niveaux requis, soft skills et fit culturel, niveau d'expérience (junior → lead), profil candidat idéal (résumé 3-5 phrases).

**RAG :** Enrichissement avec des fiches postes similaires depuis la collection `job_profiles` de ChromaDB.

---

### Agent 2 — Screening & Scoring des CVs `cv_screener.py`

| | |
|---|---|
| **Rôle** | Scorer chaque CV et produire une shortlist qualifiée |
| **Entrée** | CVs bruts (PDF/TXT) + critères du poste |
| **Sortie** | Shortlist qualifiée |
| **Formule** | `Score final = 0.7 × Score_LLM + 0.3 × Score_RAG` |

**Outputs par candidat :** compatibility score (0–1), technical & experience scores, compétences manquantes, recommandation `SHORTLIST` \| `REJECT`.

---

### Agent 3 — Génération des Questions d'Entretien `interview_generator.py`

| | |
|---|---|
| **Rôle** | Générer questions personnalisées par candidat |
| **Entrée** | Profil candidat + critères du poste |
| **Sortie** | Questions typées avec critères d'évaluation |

**Types de questions :** techniques · comportementales · situationnelles

**RAG :** Récupération de questions de référence par domaine/niveau depuis la collection `evaluation_grids`.

---

### Agent 4 — Analyse des Réponses d'Entretien `interview_analyzer.py`

| | |
|---|---|
| **Rôle** | Évaluer les réponses d'entretien |
| **Entrée** | Questions + réponses du candidat |
| **Sortie** | `InterviewEvaluation` + recommandation |

**Scores évalués :** technical score, soft skills score, problem solving score.

**Recommandation :** `HIRE` \| `WAITLIST` \| `REJECT`

**Dimensions :** maîtrise technique, communication, résolution de problèmes, fit culturel.

---

### Agent 5 — Rapport Final & Onboarding `report_generator.py`

| | |
|---|---|
| **Rôle** | Agréger tous les résultats et générer le rapport de recrutement |
| **Entrée** | Tous les scores + décisions HITL |
| **Sortie** | Rapport JSON complet + statistiques RAG + log du workflow |

**Contenu :** executive summary, ranking des candidats, candidat sélectionné, recommandations onboarding.

---

## 📚 RAG Agentique

Le **Retrieval-Augmented Generation** dans ce système est **agentique** : les agents décident eux-mêmes quand interroger la base de connaissances, via des appels de type *tool call*.

### Base vectorielle ChromaDB

Le système utilise **ChromaDB** avec des embeddings locaux (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions) organisés en **3 collections spécialisées** :

| Collection | Contenu | Utilisée par |
|-----------|---------|-------------|
| `job_profiles` | Fiches postes analysées + templates métier | Agent 1 (normalisation) + Agent 3 (contexte) |
| `cv_profiles` | CVs historiques + profils candidats recrutés | Agent 2 (matching sémantique) + Agent 4 (comparaison) |
| `evaluation_grids` | Grilles d'évaluation RH, questions de référence, modèles entretien | Agent 3 (génération contextualisée) + Agent 4 (évaluation) |

### Paramètres de recherche

| Paramètre | Valeur | Justification |
|-----------|--------|---------------|
| Embedding model | `all-MiniLM-L6-v2` | 384 dims, local, performant |
| Similarity metric | Cosine distance | Robuste + HNSW indexing |
| Default `n_results` | 3-4 documents | Équilibre précision/latence |
| Score normalization | `score = 1 − distance/2` | Conversion distance ∈ [0,2] vers score ∈ [0,1] |

### Initialisation de la base

```bash
cd recruitment-backend
$env:PYTHONPATH = "."          # PowerShell
python scripts/seed_knowledge_base.py
python scripts/init_chroma.py  # vérifier les collections
```

> **Note :** Au premier lancement, le modèle d'embedding est téléchargé par Hugging Face (~90 Mo). Si vous changez de stratégie d'embedding, supprimez `data/chroma_db/` puis relancez le seed.

---

## 🧑‍⚖️ Human-in-the-Loop (HITL)

Dans un système de recrutement, les décisions impactent directement des individus. Le HITL garantit que l'IA reste un **outil d'aide à la décision** et non un décideur autonome.

### Checkpoint 1 — Validation RH (après Agent 2)

| | |
|---|---|
| **Déclencheur** | L'Agent 2 a produit une shortlist de candidats scorés |
| **Acteur** | Responsable RH |
| **Actions** | ✅ Valider la shortlist · ❌ Rejeter des candidats sur-scorés · 💬 Ajouter un commentaire · 🚫 Clôturer sans candidat |
| **Mécanisme** | `interrupt_before=["hitl_hr_validation"]` |

### Checkpoint 2 — Décision Manager (après Agent 4)

| | |
|---|---|
| **Déclencheur** | Les entretiens ont été analysés par l'IA |
| **Acteur** | Manager / DRH |
| **Actions** | ✅ Recruter le candidat · 🔄 Relancer un second tour · 🚫 Clôturer sans recrutement · ⬆️ Escalader vers la direction |
| **Mécanisme** | `interrupt_before=["hitl_manager_validation"]` |

---

## 📊 Évaluation des Prompts

Le projet intègre un système d'**évaluation quantitative et de test A/B** des prompts, implémenté dans `scripts/evaluate_prompts.py`.

### Méthodologie

- **2 variantes** de prompts testées (A: Expert Direct vs B: Concise & Factual)
- **3 profils types** de candidats (Alice, Bob, Charlie)
- **3 essais** (trials) par profil et par variante
- Métriques : précision du scoring, complétude des justifications, stabilité (écart-type), extraction des compétences manquantes

### Résultat

> **Variante A sélectionnée** comme prompt de production : justifications riches (moy. 38 mots, 100% qualité) vs Variante B trop concise (4-6 mots, 50% qualité). Les deux variantes montrent une précision de 100% sur l'identification des compétences manquantes et une stabilité remarquable (σ < 1.5 point).

---

## 🛠 Stack Technique

| Couche | Technologie | Rôle |
|--------|------------|------|
| **Orchestration** | LangGraph 0.2.59 | StateGraph, interruptions, routeurs conditionnels |
| **LLM** | Gemini 2.5-Flash | Tous les agents (analyse, scoring, évaluation, rapport) |
| **Embeddings** | sentence-transformers 3.3.1 | `all-MiniLM-L6-v2` (384 dims, local, sans API) |
| **Vector DB** | ChromaDB 0.5.23 | Stockage persistant des 3 collections |
| **LangChain** | langchain-core 0.3.13 | Intégrations LLM, chaînes, base pour LangGraph |
| **PDF** | PyMuPDF 1.24 + pdfplumber 0.11 | Extraction texte depuis CVs PDF |
| **Validation** | Pydantic 2.10 | Modèles structurés (JobProfile, CandidateProfile, etc.) |
| **Backend** | FastAPI 0.115 | REST endpoints + WebSocket + multipart upload |
| **Serveur** | Uvicorn 0.32 | Serveur ASGI asynchrone |
| **WebSocket** | websockets 13.1 | Communication temps réel |
| **Frontend** | React 18.3 + Vite 6 | Interface utilisateur TypeScript |
| **State** | Zustand 5.0 | Gestion d'état frontend |
| **Styling** | Tailwind CSS 3.4 | Framework CSS utilitaire |
| **Animation** | Framer Motion 11.15 | Animations et transitions UI |
| **Charts** | Recharts 2.14 | Visualisation de données (radars, jauges) |
| **Icons** | Lucide React | Icônes vectorielles |

---

## 📁 Structure du Projet

```
agents-rh-recrutement/
│
├── recruitment-backend/              # Backend (FastAPI + LangGraph)
│   ├── requirements.txt
│   ├── .env.example                  # Template des variables d'environnement
│   ├── README.md
│   │
│   ├── app/                          # Code source backend
│   │   ├── main.py                   # Point d'entrée FastAPI
│   │   │
│   │   ├── agents/                   # Les 5 agents du pipeline
│   │   │   ├── job_analyzer.py           # Agent 1 : Analyse de la fiche de poste
│   │   │   ├── cv_screener.py            # Agent 2 : Tri et scoring des CVs
│   │   │   ├── interview_generator.py    # Agent 3 : Génération de questions
│   │   │   ├── interview_analyzer.py     # Agent 4 : Analyse des réponses
│   │   │   └── report_generator.py       # Agent 5 : Rapport final
│   │   │
│   │   ├── graph/                    # Orchestration LangGraph
│   │   │   ├── state.py                  # RecruitmentState (TypedDict)
│   │   │   ├── workflow.py               # Définition du graphe de flux
│   │   │   ├── nodes.py                  # Nœuds d'exécution
│   │   │   ├── edges.py                  # Transitions conditionnelles
│   │   │   └── hitl_manager.py           # Logique de validation humaine
│   │   │
│   │   ├── api/                      # Couche réseau
│   │   │   ├── websocket.py              # Endpoint WebSocket
│   │   │   ├── ws_manager.py             # Gestionnaire de connexions WS
│   │   │   ├── state_serializers.py      # Sérialisation de l'état
│   │   │   ├── events.py                # Dispatch d'événements
│   │   │   ├── pipeline.py              # Exécution du pipeline
│   │   │   └── routes/                   # Endpoints REST
│   │   │       ├── recruitment.py            # Initialisation et suivi
│   │   │       ├── hitl.py                   # Validations HITL (RH/Manager)
│   │   │       ├── upload.py                 # Upload offre et CVs
│   │   │       └── reports.py                # Export rapports finaux
│   │   │
│   │   ├── rag/                      # Moteur RAG (ChromaDB)
│   │   │   ├── retriever.py              # Recherche sémantique
│   │   │   ├── embeddings.py             # Modèle d'embeddings local
│   │   │   ├── ingestion.py              # Indexation des documents
│   │   │   └── vector_store.py           # Configuration ChromaDB
│   │   │
│   │   ├── prompts/                  # Prompts système optimisés
│   │   │   ├── job_analyzer_prompts.py
│   │   │   ├── cv_screener_prompts.py
│   │   │   ├── interview_generator_prompts.py
│   │   │   ├── interview_analyzer_prompts.py
│   │   │   ├── report_generator_prompts.py
│   │   │   └── prompt_evaluator.py       # Évaluateur de prompts
│   │   │
│   │   ├── models/                   # Schémas Pydantic
│   │   │   ├── job.py                    # JobProfile
│   │   │   ├── candidate.py              # CandidateProfile
│   │   │   ├── interview.py              # InterviewQuestions
│   │   │   ├── evaluation.py             # InterviewEvaluation
│   │   │   ├── hitl.py                   # HITLStatus, Decisions
│   │   │   └── report.py                # FinalReport
│   │   │
│   │   ├── services/                 # Services applicatifs
│   │   │   ├── gemini_service.py         # Client Gemini LLM
│   │   │   ├── pdf_service.py            # Extraction PDF (PyMuPDF)
│   │   │   ├── vector_service.py         # Service vectoriel
│   │   │   ├── session_manager.py        # Gestion des sessions
│   │   │   └── notification_service.py   # Notifications
│   │   │
│   │   ├── core/                     # Configuration globale
│   │   │   ├── config.py                 # Settings Pydantic
│   │   │   ├── dependencies.py           # Injection de dépendances
│   │   │   └── logging.py               # Logger central
│   │   │
│   │   └── utils/                    # Utilitaires
│   │
│   ├── data/
│   │   ├── knowledge_base/           # Sources documentaires RAG
│   │   │   ├── job_templates/            # Fiches de poste
│   │   │   ├── evaluation_grids/         # Grilles d'évaluation
│   │   │   └── competency_frameworks/    # Référentiels de compétences
│   │   └── chroma_db/                # Index vectoriel persistant
│   │
│   ├── scripts/
│   │   ├── evaluate_prompts.py       # Test A/B et évaluation des prompts
│   │   ├── seed_knowledge_base.py    # Ingestion initiale RAG
│   │   └── init_chroma.py            # Vérification des collections
│   │
│   └── tests/                        # Suite de tests (pytest)
│       ├── test_agents/
│       ├── test_api/
│       ├── test_integration/
│       ├── test_prompts/
│       ├── test_rag/
│       └── test_utils/
│
└── frontend/                         # Interface (React + Vite + TypeScript)
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── index.html
    │
    └── src/
        ├── main.tsx                  # Point d'entrée React
        ├── App.tsx                   # Routage et shell global
        ├── index.css                 # Tailwind + variables CSS
        │
        ├── store/
        │   └── recruitmentStore.ts   # État Zustand + actions API + WebSocket
        │
        ├── types/
        │   └── index.ts             # Types TypeScript unifiés
        │
        ├── data/                    # Données pour le développement
        │   ├── candidates.ts
        │   ├── interviews.ts
        │   ├── jobOffers.ts
        │   └── reports.ts
        │
        └── components/
            ├── layout/              # Structure de page
            │   ├── AppShell.tsx          # Shell principal
            │   ├── WorkflowStepper.tsx   # Stepper de progression
            │   └── TerminalFeed.tsx      # Terminal de logs temps réel
            │
            ├── agents/              # Vues spécifiques aux 5 agents
            │   ├── Agent1_JobAnalysis.tsx
            │   ├── Agent2_CVScreening.tsx
            │   ├── Agent3_InterviewGen.tsx
            │   ├── Agent4_InterviewAnalysis.tsx
            │   └── Agent5_FinalReport.tsx
            │
            ├── hitl/                # Interfaces de validation humaine
            │   ├── ValidationRH.tsx      # Validation RH (HITL 1)
            │   └── ValidationManager.tsx # Approbation Manager (HITL 2)
            │
            ├── rag/                 # Affichage des références RAG
            │   └── RAGReferencePanel.tsx
            │
            ├── charts/              # Visualisations de données
            │   ├── SkillsRadar.tsx       # Radar de compétences
            │   ├── CompatibilityBar.tsx  # Barre de compatibilité
            │   └── DecisionGauge.tsx     # Jauge de décision
            │
            └── shared/              # Composants réutilisables
                ├── FileDropzone.tsx      # Zone de dépôt de fichiers
                ├── StepHeader.tsx        # En-tête d'étape
                ├── ScoreGauge.tsx        # Jauge de score
                ├── LoadingOverlay.tsx    # Overlay de chargement
                ├── ProcessingModal.tsx   # Modal de traitement
                └── TypewriterText.tsx    # Effet machine à écrire
```

---

## 🚀 Installation

### Prérequis

- **Python** 3.11+
- **Node.js** 18+ et **npm**
- Clé API **Google Gemini** ([obtenir ici](https://aistudio.google.com/app/apikey))
- *(Optionnel)* Tesseract pour OCR de PDFs scannés

### 1. Backend

```bash
cd recruitment-backend

# Créer l'environnement virtuel
python -m venv .venv

# Activer (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activer (Linux/Mac)
# source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/Mac

# ⚠️ Éditer .env et renseigner GOOGLE_API_KEY
```

### 2. Base de connaissances RAG

```bash
# Depuis recruitment-backend/
$env:PYTHONPATH = "."                     # PowerShell
# export PYTHONPATH="."                   # Bash

python scripts/seed_knowledge_base.py     # Indexer les documents
python scripts/init_chroma.py             # Vérifier les collections
```

> **Premier lancement :** Le modèle d'embedding `all-MiniLM-L6-v2` (~90 Mo) sera téléchargé automatiquement par Hugging Face.

### 3. Démarrer le backend

```bash
uvicorn app.main:app --reload --port 8000
```

- 📖 **Swagger UI** : http://localhost:8000/docs
- ❤️ **Health check** : http://localhost:8000/health

### 4. Frontend

```bash
# Dans un second terminal
cd frontend
npm install
npm run dev
```

- 🖥 **Interface** : http://localhost:5173

> Le frontend attend l'API sur `http://localhost:8000` par défaut (`VITE_API_BASE_URL`).

---

## 📡 API Reference

### Parcours complet (ordre recommandé)

| # | Action | Méthode | Endpoint |
|---|--------|---------|----------|
| 1 | Connexion WebSocket | WS | `/v1/ws/{session_id}` |
| 2 | Analyser l'offre (Agent 1) | POST | `/v1/recruitment/initialize` |
| 3 | État de la session | GET | `/v1/recruitment/{session_id}` |
| 4 | Upload des CVs (→ Agent 2) | POST | `/v1/recruitment/{session_id}/upload-cvs` |
| 5 | Shortlist | GET | `/v1/recruitment/{session_id}/shortlist` |
| 6 | Validation RH (HITL 1) | POST | `/v1/recruitment/{session_id}/hitl/hr` |
| 7 | Questions d'entretien | GET | `/v1/recruitment/{session_id}/interviews/questions` |
| 8 | Soumettre les réponses | POST | `/v1/recruitment/{session_id}/interviews/submit` |
| 9 | Évaluations | GET | `/v1/recruitment/{session_id}/evaluations` |
| 10 | Décision Manager (HITL 2) | POST | `/v1/recruitment/{session_id}/hitl/manager` |
| 11 | Rapport final (Agent 5) | GET | `/v1/recruitment/{session_id}/report` |

> **Pauses automatiques du graphe :** après l'Agent 1 (`initialize`), après l'Agent 3 (questions générées → saisir les réponses), avant chaque HITL.

### Statistiques RAG

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/v1/rag/stats` | Statistiques des collections ChromaDB |

---

## 🔌 WebSocket — Streaming Temps Réel

Connectez-vous à `ws://localhost:8000/v1/ws/{session_id}` pour recevoir les événements en temps réel.

### Types de messages

| Type | Description |
|------|-------------|
| `connected` | Connexion WebSocket établie |
| `subscribed` | Session abonnée avec succès |
| `log` | Logs de progression des agents |
| `step_update` | Transition d'étape du pipeline |
| `complete` | Pipeline terminé avec résultat |
| `error` | Erreur critique |

### Replay buffer

Les événements sont **bufferisés** par session : une connexion tardive rejoue automatiquement l'historique récent avant le message `connected`.

### Ping/Pong

```json
// Client → Serveur
{"type": "ping"}

// Serveur → Client
{"type": "pong"}
```

### Exemple de message `step_update`

```json
{
  "type": "step_update",
  "session_id": "abc-123",
  "step": "CV_SCREENING_DONE",
  "data": { "shortlisted_ids": ["cand-1", "cand-2"] },
  "timestamp": "2026-05-31T12:34:58Z"
}
```

---

## 🖥 Démonstration

Le workflow complet se déroule en 7 étapes via l'interface web :

1. **Upload de l'offre** → L'Agent 1 analyse et structure automatiquement le poste
2. **Upload des CVs** (PDF/TXT) → L'Agent 2 score et produit une shortlist
3. **Validation RH** → Le responsable RH valide ou ajuste la shortlist
4. **Questions d'entretien** → L'Agent 3 génère 6 questions personnalisées par candidat
5. **Réponses & analyse** → L'Agent 4 évalue les réponses avec scoring multidimensionnel
6. **Décision Manager** → Le manager approuve, relance ou annule
7. **Rapport final** → L'Agent 5 produit le rapport consolidé avec recommandations d'onboarding

---

## 🧪 Tests

```bash
cd recruitment-backend
$env:PYTHONPATH = "."          # PowerShell
python -m pytest tests/ -v
```

La suite de tests couvre :

| Module | Couverture |
|--------|------------|
| `test_agents/` | Agents unitaires |
| `test_api/` | Endpoints REST |
| `test_integration/` | Pipeline end-to-end |
| `test_prompts/` | Évaluation et A/B testing des prompts |
| `test_rag/` | Indexation et retrieval ChromaDB |
| `test_utils/` | Utilitaires et helpers |

---

## 🔮 Perspectives

1. **Multi-poste** — Gérer plusieurs offres en parallèle avec des threads LangGraph indépendants
2. **Entretiens vidéo** — Intégrer l'analyse de transcriptions d'entretiens vidéo réels
3. **Biais algorithmique** — Ajouter un agent de détection de biais dans le processus de scoring
4. **Onboarding IA** — Étendre le workflow jusqu'à la génération du contrat et du plan d'intégration
5. **Tableau de bord analytique** — Visualisation des métriques de recrutement sur le long terme
6. **Connexion ATS** — Intégration avec des systèmes de gestion des candidatures existants (Workday, SAP HR)

---

## ⚠️ Limitations connues

- **Sessions** : stockage en mémoire (perdu au redémarrage du serveur). Checkpointer LangGraph : `MemorySaver`.
- **Embeddings** : modèle local uniquement (`all-MiniLM-L6-v2`), pas d'API d'embedding Gemini.

---

## 👥 Auteurs

Projet réalisé dans le cadre du module **Systèmes Multi-Agents et Intelligence Artificielle Distribuée** — Master SDIA.

---

## 📄 Licence

Ce projet est un travail académique. Voir le [rapport complet](Agentic_AI_Project_Report.pdf) pour plus de détails.

---

<div align="center">

**[⬆ Retour en haut](#-assistant-intelligent-de-recrutement-rh)**

</div>
