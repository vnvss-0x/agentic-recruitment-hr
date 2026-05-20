"""
Service ChromaDB — Base vectorielle & embeddings Google Gemini.

Architecture :
    VectorService orchestre trois collections ChromaDB indépendantes :

    ┌─────────────────────┬─────────────────────────────────────────────┐
    │ Collection          │ Contenu                                     │
    ├─────────────────────┼─────────────────────────────────────────────┤
    │ job_profiles        │ Anciennes fiches de poste analysées         │
    │ cv_profiles         │ CVs et profils candidats historiques        │
    │ evaluation_grids    │ Grilles RH, référentiels, modèles entretien │
    └─────────────────────┴─────────────────────────────────────────────┘

    Embeddings : Google text-embedding-004 (768 dimensions)
    Fallback   : sentence-transformers/all-MiniLM-L6-v2 (local, offline)

Usage :
    from app.services.vector_service import vector_service

    # Indexer un document
    await vector_service.add_document(
        collection="evaluation_grids",
        doc_id="grid_python_senior_001",
        content="Grille d'évaluation Python Senior...",
        metadata={"type": "evaluation_grid", "role": "python_senior"},
    )

    # Rechercher les documents les plus proches
    results = await vector_service.similarity_search(
        collection="evaluation_grids",
        query="compétences requises développeur backend python",
        n_results=3,
    )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────

COLLECTION_JOBS = "job_profiles"
COLLECTION_CVS = "cv_profiles"
COLLECTION_GRIDS = "evaluation_grids"

ALL_COLLECTIONS = [COLLECTION_JOBS, COLLECTION_CVS, COLLECTION_GRIDS]

GEMINI_EMBEDDING_MODEL = "models/text-embedding-004"
FALLBACK_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

DEFAULT_N_RESULTS = 3
MAX_N_RESULTS = 10


# ─────────────────────────────────────────────
# Types de retour
# ─────────────────────────────────────────────


@dataclass
class SearchResult:
    """Un document retrouvé par similarity search."""

    doc_id: str
    content: str
    metadata: dict[str, Any]
    distance: float  # 0.0 = identique, 2.0 = opposé (cosine)
    score: float  # 1 - distance/2, normalisé 0→1

    @classmethod
    def from_chroma(
        cls,
        doc_id: str,
        content: str,
        metadata: dict,
        distance: float,
    ) -> "SearchResult":
        score = max(0.0, min(1.0, 1.0 - distance / 2.0))
        return cls(
            doc_id=doc_id,
            content=content,
            metadata=metadata or {},
            distance=distance,
            score=score,
        )


@dataclass
class IndexResult:
    """Résultat d'une opération d'indexation."""

    doc_id: str
    collection: str
    success: bool
    error: str | None = None


# ─────────────────────────────────────────────
# Embedding functions
# ─────────────────────────────────────────────


def _build_gemini_embedding_fn(api_key: str):
    """
    Construit la fonction d'embedding Gemini pour ChromaDB.

    ChromaDB attend une EmbeddingFunction compatible avec son interface.
    On utilise l'intégration native de chromadb avec Google AI.
    """
    try:
        from chromadb.utils.embedding_functions import (
            GoogleGenerativeAiEmbeddingFunction,
        )

        fn = GoogleGenerativeAiEmbeddingFunction(
            api_key=api_key,
            model_name=GEMINI_EMBEDDING_MODEL,
        )
        logger.info(
            f"[VectorService] Embeddings Gemini initialisés ({GEMINI_EMBEDDING_MODEL})"
        )
        return fn
    except Exception as exc:
        logger.warning(
            f"[VectorService] Échec init embeddings Gemini : {exc}. "
            "Fallback sur sentence-transformers."
        )
        return None


def _build_local_embedding_fn():
    """
    Fallback : embeddings locaux via sentence-transformers.
    Ne nécessite pas de clé API — utile en mode offline / tests.
    """
    try:
        from chromadb.utils.embedding_functions import (
            SentenceTransformerEmbeddingFunction,
        )

        fn = SentenceTransformerEmbeddingFunction(model_name=FALLBACK_EMBEDDING_MODEL)
        logger.info(
            f"[VectorService] Embeddings locaux initialisés ({FALLBACK_EMBEDDING_MODEL})"
        )
        return fn
    except Exception as exc:
        logger.error(f"[VectorService] Aucun embedding disponible : {exc}")
        return None


# ─────────────────────────────────────────────
# Service principal
# ─────────────────────────────────────────────


class VectorService:
    """
    Service singleton pour toutes les opérations ChromaDB.

    Initialisation lazy : ChromaDB et les embeddings ne sont chargés
    qu'au premier appel pour ne pas ralentir le démarrage FastAPI.
    """

    def __init__(self) -> None:
        self._client = None
        self._embedding_fn = None
        self._collections: dict[str, Any] = {}
        self._initialized = False

    # ─────────────────────────────────────────
    # Initialisation
    # ─────────────────────────────────────────

    def _ensure_initialized(self) -> None:
        """Initialise ChromaDB au premier appel (lazy init)."""
        if self._initialized:
            return
        self._initialize()

    def _initialize(self) -> None:
        """
        Initialisation complète :
        1. Client ChromaDB persistant
        2. Fonction d'embedding (Gemini → fallback local)
        3. Création/récupération des trois collections
        """
        import chromadb
        from app.core.config import settings

        # ── Client ChromaDB persistant ─────────────────────────────
        chroma_path = str(settings.chroma_dir.resolve())
        Path(chroma_path).mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(path=chroma_path)
        logger.info(f"[VectorService] ChromaDB initialisé → {chroma_path}")

        # ── Fonction d'embedding ────────────────────────────────────
        api_key = settings.google_api_key
        if api_key:
            self._embedding_fn = _build_gemini_embedding_fn(api_key)
            if self._embedding_fn is not None:
                try:
                    self._embedding_fn(["healthcheck"])
                except Exception as exc:
                    logger.warning(
                        "[VectorService] Embeddings Gemini indisponibles (%s). "
                        "Fallback sentence-transformers.",
                        exc,
                    )
                    self._embedding_fn = None

        if self._embedding_fn is None:
            self._embedding_fn = _build_local_embedding_fn()

        if self._embedding_fn is None:
            raise RuntimeError(
                "Aucune fonction d'embedding disponible. "
                "Vérifiez GOOGLE_API_KEY ou installez sentence-transformers."
            )

        # ── Collections ─────────────────────────────────────────────
        for name in ALL_COLLECTIONS:
            self._collections[name] = self._client.get_or_create_collection(
                name=name,
                embedding_function=self._embedding_fn,
                metadata={"hnsw:space": "cosine"},  # similarité cosine
            )
            count = self._collections[name].count()
            logger.info(f"[VectorService] Collection '{name}' : {count} documents.")

        self._initialized = True
        logger.info("[VectorService] Initialisation complète ✅")

    def _get_collection(self, collection: str):
        """Retourne la collection ChromaDB, lève ValueError si inconnue."""
        self._ensure_initialized()
        if collection not in self._collections:
            raise ValueError(
                f"Collection inconnue : '{collection}'. "
                f"Collections disponibles : {ALL_COLLECTIONS}"
            )
        return self._collections[collection]

    # ─────────────────────────────────────────
    # Opérations publiques
    # ─────────────────────────────────────────

    async def add_document(
        self,
        collection: str,
        doc_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        upsert: bool = True,
    ) -> IndexResult:
        """
        Indexe un document dans une collection ChromaDB.

        Args:
            collection: Nom de la collection cible.
            doc_id:     Identifiant unique du document.
            content:    Texte à vectoriser et stocker.
            metadata:   Métadonnées associées (filtrables).
            upsert:     Si True, écrase le document existant avec le même ID.

        Returns:
            IndexResult indiquant le succès ou l'échec.
        """
        if not content or not content.strip():
            return IndexResult(
                doc_id=doc_id,
                collection=collection,
                success=False,
                error="Contenu vide — document non indexé.",
            )

        try:
            col = self._get_collection(collection)
            clean_metadata = _sanitise_metadata(metadata or {})

            if upsert:
                col.upsert(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[clean_metadata],
                )
            else:
                col.add(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[clean_metadata],
                )

            logger.debug(
                f"[VectorService] Document '{doc_id}' indexé " f"dans '{collection}'."
            )
            return IndexResult(doc_id=doc_id, collection=collection, success=True)

        except Exception as exc:
            error_msg = f"Erreur indexation '{doc_id}' : {exc}"
            logger.error(f"[VectorService] {error_msg}")
            return IndexResult(
                doc_id=doc_id,
                collection=collection,
                success=False,
                error=error_msg,
            )

    async def add_documents_batch(
        self,
        collection: str,
        documents: list[dict[str, Any]],
    ) -> list[IndexResult]:
        """
        Indexe plusieurs documents en une seule opération batch.

        Args:
            collection: Nom de la collection.
            documents:  Liste de dicts avec clés : id, content, metadata.

        Returns:
            Liste d'IndexResult dans le même ordre que l'entrée.
        """
        if not documents:
            return []

        results: list[IndexResult] = []
        valid_ids, valid_docs, valid_metas = [], [], []

        for doc in documents:
            doc_id = doc.get("id", "")
            content = doc.get("content", "")
            meta = doc.get("metadata", {})

            if not doc_id or not content.strip():
                results.append(
                    IndexResult(
                        doc_id=doc_id or "(vide)",
                        collection=collection,
                        success=False,
                        error="id ou content manquant.",
                    )
                )
                continue

            valid_ids.append(doc_id)
            valid_docs.append(content)
            valid_metas.append(_sanitise_metadata(meta))
            results.append(
                IndexResult(doc_id=doc_id, collection=collection, success=True)
            )

        if valid_ids:
            try:
                col = self._get_collection(collection)
                col.upsert(
                    ids=valid_ids,
                    documents=valid_docs,
                    metadatas=valid_metas,
                )
                logger.info(
                    f"[VectorService] Batch : {len(valid_ids)} documents "
                    f"indexés dans '{collection}'."
                )
            except Exception as exc:
                logger.error(f"[VectorService] Erreur batch : {exc}")
                for r in results:
                    if r.success:
                        r.success = False
                        r.error = str(exc)

        return results

    async def similarity_search(
        self,
        collection: str,
        query: str,
        n_results: int = DEFAULT_N_RESULTS,
        metadata_filter: dict[str, Any] | None = None,
        min_score: float = 0.0,
    ) -> list[SearchResult]:
        """
        Recherche les documents les plus sémantiquement proches d'une requête.

        Args:
            collection:      Nom de la collection à interroger.
            query:           Texte de la requête en langage naturel.
            n_results:       Nombre max de résultats retournés.
            metadata_filter: Filtre ChromaDB (ex: {"type": "evaluation_grid"}).
            min_score:       Score minimum pour inclure un résultat (0.0–1.0).

        Returns:
            Liste de SearchResult triée par score décroissant.
            Liste vide si la collection est vide ou aucun résultat.
        """
        if not query or not query.strip():
            return []

        n_results = min(max(1, n_results), MAX_N_RESULTS)

        try:
            col = self._get_collection(collection)

            # ChromaDB lève une exception si n_results > nombre de docs
            doc_count = col.count()
            if doc_count == 0:
                logger.debug(
                    f"[VectorService] Collection '{collection}' vide — "
                    "similarity_search ignoré."
                )
                return []

            effective_n = min(n_results, doc_count)

            query_kwargs: dict[str, Any] = {
                "query_texts": [query],
                "n_results": effective_n,
                "include": ["documents", "metadatas", "distances"],
            }
            if metadata_filter:
                query_kwargs["where"] = metadata_filter

            raw = col.query(**query_kwargs)

            # Dépaquetage des résultats ChromaDB
            ids = raw.get("ids", [[]])[0]
            docs = raw.get("documents", [[]])[0]
            metas = raw.get("metadatas", [[]])[0]
            distances = raw.get("distances", [[]])[0]

            results: list[SearchResult] = []
            for doc_id, content, meta, dist in zip(ids, docs, metas, distances):
                sr = SearchResult.from_chroma(
                    doc_id=doc_id,
                    content=content or "",
                    metadata=meta or {},
                    distance=float(dist),
                )
                if sr.score >= min_score:
                    results.append(sr)

            results.sort(key=lambda r: r.score, reverse=True)

            logger.debug(
                f"[VectorService] similarity_search '{collection}' : "
                f"{len(results)} résultat(s) pour '{query[:60]}'."
            )
            return results

        except Exception as exc:
            logger.error(
                f"[VectorService] Erreur similarity_search "
                f"collection='{collection}' : {exc}"
            )
            return []

    async def delete_document(self, collection: str, doc_id: str) -> bool:
        """Supprime un document de la collection. Retourne True si succès."""
        try:
            col = self._get_collection(collection)
            col.delete(ids=[doc_id])
            logger.debug(
                f"[VectorService] Document '{doc_id}' supprimé de '{collection}'."
            )
            return True
        except Exception as exc:
            logger.error(f"[VectorService] Erreur suppression '{doc_id}' : {exc}")
            return False

    async def get_collection_stats(self, collection: str) -> dict[str, Any]:
        """Retourne les statistiques d'une collection."""
        try:
            col = self._get_collection(collection)
            return {
                "collection": collection,
                "document_count": col.count(),
                "embedding_model": (
                    GEMINI_EMBEDDING_MODEL
                    if self._embedding_fn
                    and "Google" in type(self._embedding_fn).__name__
                    else FALLBACK_EMBEDDING_MODEL
                ),
            }
        except Exception as exc:
            return {"collection": collection, "error": str(exc)}

    async def get_all_stats(self) -> list[dict[str, Any]]:
        """Retourne les stats de toutes les collections."""
        return [await self.get_collection_stats(c) for c in ALL_COLLECTIONS]


# ─────────────────────────────────────────────
# Utilitaires
# ─────────────────────────────────────────────


def _sanitise_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    """
    ChromaDB n'accepte que str, int, float, bool comme valeurs de métadonnées.
    Convertit ou supprime les autres types.
    """
    clean: dict[str, Any] = {}
    for k, v in meta.items():
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        elif v is None:
            clean[k] = ""
        elif isinstance(v, list):
            clean[k] = ", ".join(str(i) for i in v)
        else:
            clean[k] = str(v)
    return clean


# ─────────────────────────────────────────────
# Singleton exporté
# ─────────────────────────────────────────────

vector_service = VectorService()
