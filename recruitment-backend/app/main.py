"""
Point d'entrée FastAPI — Recruitment AI Backend.

Endpoints disponibles :
    GET  /health                          → Santé du serveur
    GET  /v1/info                         → Informations de l'API
    POST /v1/recruitment/initialize       → Lance le pipeline (Agent 1)
    WS   /v1/ws/{session_id}             → Stream temps réel des logs

Démarrage local :
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ── Imports internes ───────────────────────────────────────────────
from app.core.config import settings
from app.graph.state import PipelineStep, RecruitmentState, create_initial_state
from app.graph.workflow import recruitment_graph
from app.models.job import RawJobOffer
from app.services.pdf_service import PDFExtractionError, pdf_service

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Gestionnaire de connexions WebSocket
# ─────────────────────────────────────────────


class WebSocketManager:
    """
    Gère les connexions WebSocket actives par session_id.

    Chaque session de recrutement peut avoir exactement une connexion
    WebSocket ouverte pour recevoir les logs temps réel du pipeline.

    Usage :
        ws_manager = WebSocketManager()
        await ws_manager.connect(session_id, websocket)
        await ws_manager.broadcast(session_id, {"type": "log", "message": "..."})
        ws_manager.disconnect(session_id)
    """

    def __init__(self) -> None:
        # {session_id: WebSocket}
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[session_id] = websocket
        logger.info(f"[WS] Connexion ouverte — session {session_id}")

    def disconnect(self, session_id: str) -> None:
        self._connections.pop(session_id, None)
        logger.info(f"[WS] Connexion fermée — session {session_id}")

    async def send(self, session_id: str, payload: dict[str, Any]) -> None:
        """Envoie un message JSON à la session si elle est connectée."""
        ws = self._connections.get(session_id)
        if ws:
            try:
                await ws.send_json(payload)
            except Exception as exc:
                logger.warning(f"[WS] Échec d'envoi vers session {session_id} : {exc}")
                self.disconnect(session_id)

    async def broadcast_log(self, session_id: str, message: str) -> None:
        """Raccourci pour envoyer un message de log au frontend."""
        await self.send(
            session_id,
            {
                "type": "log",
                "session_id": session_id,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def broadcast_step(
        self,
        session_id: str,
        step: PipelineStep,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Notifie le frontend d'un changement d'étape du pipeline."""
        await self.send(
            session_id,
            {
                "type": "step_update",
                "session_id": session_id,
                "step": step.value,
                "data": data or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def broadcast_error(self, session_id: str, message: str) -> None:
        """Notifie le frontend d'une erreur critique."""
        await self.send(
            session_id,
            {
                "type": "error",
                "session_id": session_id,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def broadcast_complete(
        self,
        session_id: str,
        result: dict[str, Any],
    ) -> None:
        """Notifie le frontend que le pipeline (ou l'étape) est terminé."""
        await self.send(
            session_id,
            {
                "type": "complete",
                "session_id": session_id,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @property
    def active_count(self) -> int:
        return len(self._connections)


ws_manager = WebSocketManager()


# ─────────────────────────────────────────────
# Lifespan (startup / shutdown)
# ─────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Exécuté au démarrage et à l'arrêt de l'application.
    Crée les répertoires nécessaires et vérifie la config.
    """
    # ── Startup ───────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info(f"  {settings.app_name} v{settings.app_version}")
    logger.info("=" * 60)

    # Création des répertoires de données
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    (settings.upload_dir / "cvs").mkdir(exist_ok=True)
    (settings.upload_dir / "jobs").mkdir(exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"  Répertoires initialisés : {settings.upload_dir}")

    # Vérification clé API Gemini
    if not settings.google_api_key:
        logger.warning(
            "  ⚠️  GOOGLE_API_KEY non définie — " "l'Agent 1 échouera à l'appel LLM."
        )
    else:
        masked = settings.google_api_key[:8] + "..." + settings.google_api_key[-4:]
        logger.info(f"  Gemini API Key : {masked}")

    # Positionnement de la clé dans l'environnement pour LangChain
    os.environ["GOOGLE_API_KEY"] = settings.google_api_key

    logger.info("  Graphe LangGraph : prêt")
    logger.info("  Serveur démarré ✅")
    logger.info("=" * 60)

    yield  # ← L'application tourne ici

    # ── Shutdown ──────────────────────────────────────────────────
    logger.info("[Shutdown] Fermeture du serveur...")


# ─────────────────────────────────────────────
# Application FastAPI
# ─────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend du système multi-agents de recrutement RH. "
        "Orchestré par LangGraph avec Google Gemini Flash."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS (pour le frontend React en dev) ──────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server (CRA)
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Schémas de réponse
# ─────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    active_ws_connections: int


class InitializeResponse(BaseModel):
    session_id: str
    status: str
    current_step: str
    job_profile: dict[str, Any] | None
    activity_log: list[str]
    errors: list[dict] | None
    extraction_method: str
    page_count: int
    char_count: int
    duration_ms: float


# ─────────────────────────────────────────────
# Routes système
# ─────────────────────────────────────────────


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Système"],
    summary="Vérification de l'état du serveur",
)
async def health_check() -> HealthResponse:
    """
    Endpoint de santé — utilisé par les load balancers et le frontend
    pour vérifier que le serveur est opérationnel.
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc).isoformat(),
        active_ws_connections=ws_manager.active_count,
    )


@app.get(
    f"{settings.api_prefix}/info",
    tags=["Système"],
    summary="Informations de l'API",
)
async def api_info() -> dict[str, Any]:
    """Retourne les métadonnées de l'API et la configuration active."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "gemini_configured": bool(settings.google_api_key),
        "max_upload_mb": settings.max_upload_size_mb,
        "allowed_extensions": settings.allowed_extensions,
        "pipeline_steps": [s.value for s in PipelineStep],
        "docs": "/docs",
    }


# ─────────────────────────────────────────────
# Route principale — Initialisation du pipeline
# ─────────────────────────────────────────────


@app.post(
    f"{settings.api_prefix}/recruitment/initialize",
    response_model=InitializeResponse,
    tags=["Recrutement"],
    summary="Initialise une session de recrutement et lance l'Agent 1",
    status_code=status.HTTP_200_OK,
)
async def initialize_recruitment(
    file: UploadFile = File(
        ...,
        description="Offre d'emploi au format PDF ou TXT.",
    ),
    job_title: str = Form(
        default="",
        description="Intitulé du poste (optionnel, extrait du PDF si absent).",
    ),
    company_name: str = Form(
        default="",
        description="Nom de l'entreprise (optionnel).",
    ),
) -> InitializeResponse:
    """
    Lance le pipeline de recrutement complet depuis une offre d'emploi.

    Étapes exécutées par cet endpoint :
        1. Validation et extraction du texte PDF/TXT.
        2. Construction du RecruitmentState initial.
        3. Exécution du graphe LangGraph (Agent 1 → placeholders).
        4. Retour du JobProfile structuré généré par l'Agent 1.

    Le `session_id` retourné permet ensuite de :
        - Se connecter au WebSocket (/v1/ws/{session_id})
        - Envoyer les CVs (/v1/recruitment/{session_id}/upload-cvs)
        - Valider les HITL (/v1/recruitment/{session_id}/hitl/*)
    """
    start_time = datetime.now(timezone.utc)

    # ── 1. Lecture du fichier uploadé ─────────────────────────────
    filename = file.filename or "document.pdf"
    file_bytes = await file.read()

    logger.info(
        f"[/initialize] Fichier reçu : '{filename}' "
        f"({len(file_bytes) / 1024:.1f} KB)"
    )

    # ── 2. Validation du fichier ───────────────────────────────────
    try:
        pdf_service.validate_file(
            file_bytes=file_bytes,
            filename=filename,
            max_bytes=settings.max_upload_bytes,
        )
    except ValueError as exc:
        logger.warning(f"[/initialize] Validation échouée : {exc}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # ── 3. Extraction du texte ─────────────────────────────────────
    try:
        extraction = await pdf_service.extract(
            file_bytes=file_bytes,
            filename=filename,
        )
    except PDFExtractionError as exc:
        logger.error(f"[/initialize] Extraction échouée : {exc}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Impossible d'extraire le texte du fichier : {exc}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    logger.info(
        f"[/initialize] Extraction OK via {extraction.method_used.value} : "
        f"{extraction.page_count} pages, {extraction.char_count} caractères."
    )

    # ── 4. Construction de l'offre brute ──────────────────────────
    raw_offer = RawJobOffer(
        title=job_title or filename.replace(".pdf", "").replace(".txt", ""),
        raw_text=extraction.text,
        source_filename=filename,
        company_name=company_name or None,
    )

    # ── 5. Génération du session_id ───────────────────────────────
    session_id = str(uuid.uuid4())
    created_at = start_time.isoformat()

    logger.info(f"[/initialize] Session créée : {session_id}")

    # ── 6. Initialisation du RecruitmentState ─────────────────────
    initial_state = create_initial_state(
        session_id=session_id,
        raw_job_offer=raw_offer,
        raw_cvs=[],  # Les CVs seront uploadés dans une étape suivante
        created_at=created_at,
    )

    # ── 7. Configuration LangGraph (thread par session) ───────────
    langgraph_config = {
        "configurable": {
            "thread_id": session_id,  # Isole chaque session dans son propre thread
        },
        "recursion_limit": settings.langgraph_recursion_limit,
    }

    # ── 8. Exécution du graphe LangGraph ──────────────────────────
    logger.info(f"[/initialize] Démarrage du graphe LangGraph — session {session_id}")

    try:
        final_state: RecruitmentState = recruitment_graph.invoke(
            initial_state,
            config=langgraph_config,
        )
    except Exception as exc:
        logger.exception(f"[/initialize] Erreur LangGraph : {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne du pipeline LangGraph : {exc}",
        )

    # ── 9. Extraction des résultats du state final ─────────────────
    job_profile = final_state.get("job_profile")
    current_step = final_state.get("current_step", PipelineStep.INITIALIZED)
    activity_log = final_state.get("activity_log") or []
    errors = final_state.get("errors") or []

    has_error = final_state.get("has_critical_error", False)
    if has_error:
        logger.error(
            f"[/initialize] Pipeline terminé avec erreur — session {session_id}"
        )

    # ── 10. Calcul de la durée ─────────────────────────────────────
    end_time = datetime.now(timezone.utc)
    duration_ms = (end_time - start_time).total_seconds() * 1000

    logger.info(
        f"[/initialize] Pipeline terminé en {duration_ms:.0f}ms — "
        f"étape : {current_step.value if isinstance(current_step, PipelineStep) else current_step} — "
        f"session {session_id}"
    )

    # ── 11. Sérialisation du JobProfile ───────────────────────────
    job_profile_dict: dict[str, Any] | None = None
    if job_profile:
        # Pydantic v2 : model_dump() avec gestion des Enums
        job_profile_dict = job_profile.model_dump(mode="json")

    # ── 12. Retour HTTP ───────────────────────────────────────────
    return InitializeResponse(
        session_id=session_id,
        status="error" if has_error else "success",
        current_step=(
            current_step.value
            if isinstance(current_step, PipelineStep)
            else str(current_step)
        ),
        job_profile=job_profile_dict,
        activity_log=activity_log,
        errors=(
            [
                {
                    "step": e.get("step", ""),
                    "agent": e.get("agent", ""),
                    "message": e.get("message", ""),
                    "recoverable": e.get("recoverable", False),
                }
                for e in errors
            ]
            if errors
            else None
        ),
        extraction_method=extraction.method_used.value,
        page_count=extraction.page_count,
        char_count=extraction.char_count,
        duration_ms=round(duration_ms, 2),
    )


# ─────────────────────────────────────────────
# WebSocket — Logs temps réel
# ─────────────────────────────────────────────


@app.websocket(f"{settings.api_prefix}/ws/{{session_id}}")
async def websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
    """
    WebSocket de suivi temps réel d'une session de recrutement.

    Protocole de messages (JSON) :

        → Client envoie :
            {"type": "ping"}
            {"type": "subscribe", "session_id": "..."}

        ← Serveur émet :
            {"type": "connected", "session_id": "...", "timestamp": "..."}
            {"type": "log",         "message": "...", "timestamp": "..."}
            {"type": "step_update", "step": "...",    "data": {...}}
            {"type": "error",       "message": "...", "timestamp": "..."}
            {"type": "complete",    "result": {...},  "timestamp": "..."}
            {"type": "pong",        "timestamp": "..."}

    Le WebSocket reste ouvert pendant toute la durée de la session.
    Le client React se reconnecte automatiquement si la connexion est perdue.
    """
    await ws_manager.connect(session_id, websocket)

    # Message de bienvenue
    await ws_manager.send(
        session_id,
        {
            "type": "connected",
            "session_id": session_id,
            "message": (
                f"Connecté à la session de recrutement {session_id}. "
                "En attente des événements du pipeline..."
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    try:
        # Boucle de réception — maintient la connexion ouverte
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "ping":
                # Keepalive — répond avec pong
                await ws_manager.send(
                    session_id,
                    {
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )

            elif msg_type == "subscribe":
                # Le client confirme son abonnement à une session
                logger.info(f"[WS] Client abonné à la session {session_id}")
                await ws_manager.send(
                    session_id,
                    {
                        "type": "subscribed",
                        "session_id": session_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )

            else:
                logger.debug(
                    f"[WS] Message inconnu de la session {session_id} : {data}"
                )

    except WebSocketDisconnect:
        logger.info(f"[WS] Client déconnecté — session {session_id}")
    except Exception as exc:
        logger.error(f"[WS] Erreur — session {session_id} : {exc}")
    finally:
        ws_manager.disconnect(session_id)


# ─────────────────────────────────────────────
# Gestionnaire d'erreurs global
# ─────────────────────────────────────────────


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """
    Capture toute exception non gérée et retourne une réponse JSON propre
    plutôt qu'une stack trace HTML en production.
    """
    logger.exception(f"Exception non gérée sur {request.url} : {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": (
                str(exc) if settings.debug else "Une erreur interne est survenue."
            ),
            "path": str(request.url),
        },
    )
