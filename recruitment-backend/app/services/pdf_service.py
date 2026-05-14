"""
Service d'extraction de texte PDF.

Stratégie à trois niveaux (du plus rapide au plus robuste) :

    Niveau 1 — PyMuPDF (fitz)
        Extraction native, très rapide, gère 95 % des PDFs modernes.
        Préféré pour sa performance et sa fidélité au layout.

    Niveau 2 — pdfplumber  [fallback automatique]
        Meilleure gestion des tableaux et des PDFs à colonnes multiples.
        Utilisé si PyMuPDF produit moins de MIN_CHARS_THRESHOLD caractères.

    Niveau 3 — Tesseract OCR  [fallback si PDF scanné]
        Converti chaque page en image puis applique l'OCR.
        Déclenché si les deux premières méthodes échouent (PDF scanné).

Usage :
    from app.services.pdf_service import pdf_service

    result = await pdf_service.extract(file_bytes, filename="offre.pdf")
    print(result.text)          # Texte brut extrait
    print(result.method_used)   # "pymupdf" | "pdfplumber" | "ocr"
    print(result.page_count)    # Nombre de pages
"""

from __future__ import annotations

import io
import logging
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

# Seuil minimal de caractères exploitables par niveau d'extraction.
# En-dessous de ce seuil on tente le niveau suivant.
MIN_CHARS_THRESHOLD = 100


# ─────────────────────────────────────────────
# Types de retour
# ─────────────────────────────────────────────


class ExtractionMethod(str, Enum):
    PYMUPDF = "pymupdf"
    PDFPLUMBER = "pdfplumber"
    OCR = "ocr"
    PLAIN_TEXT = "plain_text"


@dataclass
class ExtractionResult:
    """Résultat complet d'une extraction de fichier."""

    text: str
    method_used: ExtractionMethod
    page_count: int = 0
    char_count: int = 0
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.char_count = len(self.text)


class PDFExtractionError(Exception):
    """Levée quand aucune méthode ne parvient à extraire du texte."""


# ─────────────────────────────────────────────
# Utilitaires internes
# ─────────────────────────────────────────────


def _clean_text(raw: str) -> str:
    """
    Normalise le texte extrait :
    - Normalisation Unicode NFC
    - Suppression des caractères de contrôle invisibles
    - Collapse des lignes vides excessives (max 2 consécutives)
    - Strip global
    """
    # Normalisation Unicode
    text = unicodedata.normalize("NFC", raw)

    # Suppression caractères de contrôle (sauf \n \t)
    text = "".join(
        ch
        for ch in text
        if unicodedata.category(ch) not in ("Cc", "Cf") or ch in ("\n", "\t")
    )

    # Collapse des lignes vides excessives
    lines = text.splitlines()
    cleaned_lines: list[str] = []
    blank_streak = 0
    for line in lines:
        if line.strip() == "":
            blank_streak += 1
            if blank_streak <= 2:
                cleaned_lines.append("")
        else:
            blank_streak = 0
            cleaned_lines.append(line.rstrip())

    return "\n".join(cleaned_lines).strip()


def _is_sufficient(text: str) -> bool:
    """Retourne True si le texte extrait est exploitable."""
    return len(text.strip()) >= MIN_CHARS_THRESHOLD


# ─────────────────────────────────────────────
# Niveau 1 — PyMuPDF
# ─────────────────────────────────────────────


def _extract_with_pymupdf(pdf_bytes: bytes) -> tuple[str, int]:
    """
    Extrait le texte avec PyMuPDF (fitz).

    Returns:
        (texte_brut, nombre_de_pages)

    Raises:
        ImportError: Si PyMuPDF n'est pas installé.
        Exception:   Si le PDF est corrompu ou protégé.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = len(doc)
    parts: list[str] = []

    for page_num in range(page_count):
        page = doc[page_num]
        # "text" → texte brut avec sauts de ligne naturels
        page_text = page.get_text("text")
        if page_text.strip():
            parts.append(f"[Page {page_num + 1}]\n{page_text}")

    doc.close()
    return "\n\n".join(parts), page_count


# ─────────────────────────────────────────────
# Niveau 2 — pdfplumber
# ─────────────────────────────────────────────


def _extract_with_pdfplumber(pdf_bytes: bytes) -> tuple[str, int]:
    """
    Extrait le texte avec pdfplumber.
    Meilleur que PyMuPDF pour les colonnes et les tableaux.

    Returns:
        (texte_brut, nombre_de_pages)
    """
    import pdfplumber

    parts: list[str] = []
    page_count = 0

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        page_count = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
            if text.strip():
                parts.append(f"[Page {i + 1}]\n{text}")

    return "\n\n".join(parts), page_count


# ─────────────────────────────────────────────
# Niveau 3 — OCR Tesseract
# ─────────────────────────────────────────────


def _extract_with_ocr(pdf_bytes: bytes) -> tuple[str, int]:
    """
    Extrait le texte via OCR Tesseract (pour PDFs scannés).

    Nécessite :
        - Pillow
        - pytesseract
        - PyMuPDF (pour la conversion page → image)
        - Tesseract installé sur le système (apt/brew)

    Returns:
        (texte_ocr, nombre_de_pages)

    Raises:
        ImportError: Si pytesseract ou Pillow ne sont pas disponibles.
    """
    import fitz
    import pytesseract
    from PIL import Image

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = len(doc)
    parts: list[str] = []

    for page_num in range(page_count):
        page = doc[page_num]
        # Rendu de la page en image (300 DPI pour bonne qualité OCR)
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")

        img = Image.open(io.BytesIO(img_data))
        # lang="fra+eng" : priorité français + fallback anglais
        ocr_text = pytesseract.image_to_string(img, lang="fra+eng")

        if ocr_text.strip():
            parts.append(f"[Page {page_num + 1} — OCR]\n{ocr_text}")

    doc.close()
    return "\n\n".join(parts), page_count


# ─────────────────────────────────────────────
# Niveau 0 — Texte brut (.txt)
# ─────────────────────────────────────────────


def _extract_plain_text(file_bytes: bytes, filename: str) -> ExtractionResult:
    """
    Décode directement un fichier .txt.
    Essaie UTF-8, puis latin-1 en fallback.
    """
    warnings: list[str] = []
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1")
        warnings.append("Encodage latin-1 utilisé (UTF-8 invalide).")

    cleaned = _clean_text(text)
    if not _is_sufficient(cleaned):
        raise PDFExtractionError(
            f"Le fichier texte '{filename}' est vide ou trop court "
            f"({len(cleaned)} caractères < {MIN_CHARS_THRESHOLD})."
        )

    return ExtractionResult(
        text=cleaned,
        method_used=ExtractionMethod.PLAIN_TEXT,
        page_count=1,
        warnings=warnings,
    )


# ─────────────────────────────────────────────
# Service principal
# ─────────────────────────────────────────────


class PDFService:
    """
    Service singleton d'extraction de texte.

    Orchestre les trois niveaux d'extraction et expose
    une interface unifiée pour main.py et les agents.
    """

    async def extract(
        self,
        file_bytes: bytes,
        filename: str = "document.pdf",
    ) -> ExtractionResult:
        """
        Point d'entrée principal — extrait le texte d'un PDF ou .txt.

        Sélectionne automatiquement la méthode en cascade :
            .txt  → décodage direct
            .pdf  → PyMuPDF → pdfplumber → OCR

        Args:
            file_bytes: Contenu binaire du fichier.
            filename:   Nom du fichier (utilisé pour détecter l'extension).

        Returns:
            ExtractionResult avec le texte nettoyé et les métadonnées.

        Raises:
            PDFExtractionError: Si aucune méthode ne produit de texte valide.
            ValueError:         Si le fichier est vide ou l'extension invalide.
        """
        if not file_bytes:
            raise ValueError(f"Le fichier '{filename}' est vide.")

        ext = Path(filename).suffix.lower()

        # ── Fichier texte brut ─────────────────────────────────────
        if ext == ".txt":
            logger.info(f"[PDFService] Extraction texte brut : '{filename}'")
            return _extract_plain_text(file_bytes, filename)

        # ── Fichier PDF ────────────────────────────────────────────
        if ext != ".pdf":
            raise ValueError(
                f"Extension '{ext}' non supportée. " "Formats acceptés : .pdf, .txt"
            )

        return await self._extract_pdf(file_bytes, filename)

    async def _extract_pdf(
        self,
        pdf_bytes: bytes,
        filename: str,
    ) -> ExtractionResult:
        """
        Orchestration des trois niveaux d'extraction PDF.
        Méthode interne — utiliser extract() depuis l'extérieur.
        """
        warnings: list[str] = []

        # ── Niveau 1 : PyMuPDF ────────────────────────────────────
        try:
            logger.info(f"[PDFService] Tentative PyMuPDF : '{filename}'")
            raw_text, page_count = _extract_with_pymupdf(pdf_bytes)
            cleaned = _clean_text(raw_text)

            if _is_sufficient(cleaned):
                logger.info(
                    f"[PDFService] PyMuPDF OK : {page_count} pages, "
                    f"{len(cleaned)} caractères."
                )
                return ExtractionResult(
                    text=cleaned,
                    method_used=ExtractionMethod.PYMUPDF,
                    page_count=page_count,
                    warnings=warnings,
                )

            logger.warning(
                f"[PDFService] PyMuPDF insuffisant ({len(cleaned)} chars) "
                "— passage à pdfplumber."
            )
            warnings.append(f"PyMuPDF : seulement {len(cleaned)} caractères extraits.")

        except ImportError:
            logger.warning("[PDFService] PyMuPDF non disponible.")
            warnings.append("PyMuPDF non installé.")
        except Exception as exc:
            logger.warning(f"[PDFService] PyMuPDF échoué : {exc}")
            warnings.append(f"PyMuPDF erreur : {exc}")

        # ── Niveau 2 : pdfplumber ─────────────────────────────────
        try:
            logger.info(f"[PDFService] Tentative pdfplumber : '{filename}'")
            raw_text, page_count = _extract_with_pdfplumber(pdf_bytes)
            cleaned = _clean_text(raw_text)

            if _is_sufficient(cleaned):
                logger.info(
                    f"[PDFService] pdfplumber OK : {page_count} pages, "
                    f"{len(cleaned)} caractères."
                )
                return ExtractionResult(
                    text=cleaned,
                    method_used=ExtractionMethod.PDFPLUMBER,
                    page_count=page_count,
                    warnings=warnings,
                )

            logger.warning(
                f"[PDFService] pdfplumber insuffisant ({len(cleaned)} chars) "
                "— passage à l'OCR."
            )
            warnings.append(
                f"pdfplumber : seulement {len(cleaned)} caractères extraits."
            )

        except ImportError:
            logger.warning("[PDFService] pdfplumber non disponible.")
            warnings.append("pdfplumber non installé.")
        except Exception as exc:
            logger.warning(f"[PDFService] pdfplumber échoué : {exc}")
            warnings.append(f"pdfplumber erreur : {exc}")

        # ── Niveau 3 : OCR Tesseract ──────────────────────────────
        try:
            logger.info(f"[PDFService] Tentative OCR Tesseract : '{filename}'")
            warnings.append(
                "PDF scanné détecté — OCR Tesseract activé " "(traitement plus lent)."
            )
            raw_text, page_count = _extract_with_ocr(pdf_bytes)
            cleaned = _clean_text(raw_text)

            if _is_sufficient(cleaned):
                logger.info(
                    f"[PDFService] OCR OK : {page_count} pages, "
                    f"{len(cleaned)} caractères."
                )
                return ExtractionResult(
                    text=cleaned,
                    method_used=ExtractionMethod.OCR,
                    page_count=page_count,
                    warnings=warnings,
                )

            warnings.append(f"OCR : seulement {len(cleaned)} caractères.")

        except ImportError as exc:
            logger.warning(f"[PDFService] OCR non disponible : {exc}")
            warnings.append(f"Tesseract/Pillow non installé : {exc}")
        except Exception as exc:
            logger.error(f"[PDFService] OCR échoué : {exc}")
            warnings.append(f"OCR erreur : {exc}")

        # ── Échec total ────────────────────────────────────────────
        raise PDFExtractionError(
            f"Impossible d'extraire du texte exploitable depuis '{filename}'. "
            f"Méthodes tentées : PyMuPDF, pdfplumber, OCR. "
            f"Détails : {' | '.join(warnings)}"
        )

    def validate_file(
        self,
        file_bytes: bytes,
        filename: str,
        max_bytes: int,
    ) -> None:
        """
        Valide un fichier avant extraction.

        Vérifie :
            - Taille maximale autorisée
            - Extension dans la liste blanche
            - En-tête PDF valide (magic bytes)

        Raises:
            ValueError: Si une validation échoue.
        """
        # Taille
        if len(file_bytes) > max_bytes:
            raise ValueError(
                f"Fichier trop volumineux : {len(file_bytes) / 1_048_576:.1f} MB "
                f"(max {max_bytes / 1_048_576:.0f} MB)."
            )

        # Extension
        ext = Path(filename).suffix.lower()
        if ext not in (".pdf", ".txt"):
            raise ValueError(
                f"Extension '{ext}' non supportée. " "Formats acceptés : .pdf, .txt"
            )

        # Magic bytes PDF (%PDF-)
        if ext == ".pdf" and not file_bytes.startswith(b"%PDF-"):
            raise ValueError(
                f"Le fichier '{filename}' n'est pas un PDF valide "
                "(en-tête %PDF- manquant)."
            )


# ─────────────────────────────────────────────
# Singleton exporté
# ─────────────────────────────────────────────
pdf_service = PDFService()
