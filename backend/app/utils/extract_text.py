from __future__ import annotations

import io
from typing import Optional

from docx import Document
from pypdf import PdfReader


def extract_text_from_upload(filename: str, content_type: Optional[str], data: bytes) -> str:
    name = (filename or "").lower()
    ctype = (content_type or "").lower()

    if name.endswith(".pdf") or ctype == "application/pdf":
        reader = PdfReader(io.BytesIO(data))
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts).strip()

    if name.endswith(".docx") or ctype in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ):
        doc = Document(io.BytesIO(data))
        return "\n".join([p.text for p in doc.paragraphs]).strip()

    if name.endswith(".txt") or ctype.startswith("text/") or not ctype:
        # best effort for plain text
        try:
            return data.decode("utf-8").strip()
        except UnicodeDecodeError:
            return data.decode("latin-1", errors="ignore").strip()

    raise ValueError("Unsupported file type. Upload PDF, DOCX, or TXT.")

