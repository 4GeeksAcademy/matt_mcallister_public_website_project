"""PDF/text helpers for RFP intake."""

from __future__ import annotations

from pathlib import Path


def extract_document_text(path: str | Path) -> str:
    """Extract text from an uploaded RFP document."""
    file_path = Path(path)
    raw = file_path.read_bytes()
    if file_path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
            from io import BytesIO

            reader = PdfReader(BytesIO(raw))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages).strip()
            if text:
                return text
        except Exception:
            pass
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="ignore")


def compute_readability_metrics(text: str) -> dict[str, float | int | str]:
    words = text.split()
    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    avg_word_length = sum(len(word) for word in words) / max(len(words), 1)
    flesch = max(0.0, 206.835 - 1.015 * (len(words) / sentences) - 84.6 * (avg_word_length / 5.0))
    return {
        "word_count": len(words),
        "sentence_count": sentences,
        "flesch_reading_ease": round(flesch, 2),
        "method": "proxy_flesch",
    }
