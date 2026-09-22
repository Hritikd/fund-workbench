from __future__ import annotations

import io
import json
import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from .models import Source, SourceType

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def read_document(name: str, raw: bytes) -> str:
    """Extract text from a supported document without persisting it."""
    suffix = Path(name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix or 'none'}")
    if suffix in {".txt", ".md"}:
        return raw.decode("utf-8", errors="replace").strip()
    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(raw))
        return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
    document = Document(io.BytesIO(raw))
    return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "source"


def source_from_file(
    name: str,
    raw: bytes,
    source_type: SourceType = SourceType.COMPANY,
    url: str | None = None,
) -> Source:
    return Source(
        id=slugify(Path(name).stem),
        title=Path(name).stem.replace("_", " ").replace("-", " ").title(),
        source_type=source_type,
        content=read_document(name, raw),
        url=url,
    )


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(data: object) -> str:
    if hasattr(data, "model_dump_json"):
        return data.model_dump_json(indent=2)
    return json.dumps(data, indent=2, ensure_ascii=False)
