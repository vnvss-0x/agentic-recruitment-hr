# Recruitment AI Backend

API FastAPI + LangGraph pour le pipeline multi-agents de recrutement RH (Gemini, ChromaDB RAG, HITL).

## Prérequis

- Python 3.11+
- Clé API Google Gemini (`GOOGLE_API_KEY`)
- (Optionnel) Tesseract pour OCR PDF scannés

## Installation

```bash
cd recruitment-backend
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Éditer .env : GOOGLE_API_KEY=...
```

## Base de connaissances RAG

```bash
# Fichiers .txt / .md / .json dans :
#   data/knowledge_base/job_templates/
#   data/knowledge_base/evaluation_grids/
#   data/knowledge_base/competency_frameworks/
$env:PYTHONPATH = "."
python scripts/seed_knowledge_base.py
python scripts/init_chroma.py   # vérifier les collections
```

## Démarrer l'API

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger : http://localhost:8000/docs  
- Santé : http://localhost:8000/health  

## Frontend React minimal

Un frontend Vite/React est disponible dans `frontend/` pour piloter le backend.

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Le frontend attend par défaut l'API sur `http://localhost:8000` via `VITE_API_BASE_URL`.

## Parcours API (frontend)

| Ordre | Action | Endpoint |
|-------|--------|----------|
| 1 | (Recommandé) WebSocket | `WS /v1/ws/{session_id}` — replay des événements bufferisés |
| 2 | Analyser l'offre (Agent 1) | `POST /v1/recruitment/initialize` |
| 3 | État session | `GET /v1/recruitment/{session_id}` |
| 4 | Upload CVs | `POST /v1/recruitment/{session_id}/upload-cvs` |
| 5 | Shortlist | `GET /v1/recruitment/{session_id}/shortlist` |
| 6 | HITL RH | `POST /v1/recruitment/{session_id}/hitl/hr` |
| 7 | Questions entretien | `GET /v1/recruitment/{session_id}/interviews/questions` |
| 8 | **Réponses entretien** (obligatoire avant analyse) | `POST /v1/recruitment/{session_id}/interviews/submit` |
| 9 | Évaluations | `GET /v1/recruitment/{session_id}/evaluations` |
| 10 | HITL Manager | `POST /v1/recruitment/{session_id}/hitl/manager` |
| 11 | Rapport | `GET /v1/recruitment/{session_id}/report` |

Pauses automatiques du graphe : après l'Agent 1 (`initialize`), après l'Agent 3 (questions générées → saisir les réponses), avant chaque HITL.

## WebSocket

Messages serveur : `connected`, `log`, `step_update`, `error`, `complete`.  
Les événements sont **bufferisés** par session : une connexion tardive rejoue l'historique récent avant le message `connected`.

Client → `{"type":"ping"}` → `pong`.

## Tests

```bash
$env:PYTHONPATH = "."
python -m pytest tests/ -v
```

## RAG — Embeddings

Le vector store utilise **uniquement** le modèle local `sentence-transformers/all-MiniLM-L6-v2` (pas d'API d'embedding Gemini).  
Au premier lancement, le modèle est téléchargé par Hugging Face (~90 Mo).

Si vous changez de stratégie d'embedding, supprimez `data/chroma_db/` puis relancez `python scripts/seed_knowledge_base.py`.

## Limitations connues

- **Sessions** : stockage en mémoire (perdu au redémarrage du serveur). Checkpointer LangGraph : `MemorySaver`.

## Structure

```
app/
  agents/          # 5 agents LangGraph
  graph/           # workflow, state, HITL
  api/routes/      # REST + pipeline
  rag/             # retriever ChromaDB
  services/        # PDF, vector, sessions
data/
  knowledge_base/  # sources RAG
  chroma_db/       # index vectoriel
```
