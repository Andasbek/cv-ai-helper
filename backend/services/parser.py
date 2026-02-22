import re
from pathlib import Path


def extract_text_from_pdf(path: str) -> str:
    import pdfplumber
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
    return "\n".join(text_parts)


def extract_text_from_txt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def extract_text_from_docx(path: str) -> str:
    from docx import Document
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def normalize_text(text: str) -> str:
    # Replace Windows line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse 3+ consecutive newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove trailing spaces on each line
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)
    # Collapse multiple spaces (not newlines)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def extract_text(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        raw = extract_text_from_pdf(path)
    elif ext == ".txt":
        raw = extract_text_from_txt(path)
    elif ext == ".docx":
        raw = extract_text_from_docx(path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
    return normalize_text(raw)
