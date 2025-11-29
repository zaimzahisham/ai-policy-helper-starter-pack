import os, re, hashlib
from typing import List, Dict, Tuple
from .settings import settings

def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _detect_section_priority(section_title: str) -> str:
    """Detect section priority based on keywords. Returns 'high', 'medium', or 'low'."""
    if not section_title:
        return "low"
    title_lower = section_title.lower()
    # High priority: critical policy sections
    high_priority_keywords = ["sla", "policy", "terms", "conditions", "refund", "warranty", "compliance"]
    # Medium priority: important but less critical
    medium_priority_keywords = ["guide", "catalog", "exclusions", "cut-off", "shipping", "delivery"]
    
    for keyword in high_priority_keywords:
        if keyword in title_lower:
            return "high"
    for keyword in medium_priority_keywords:
        if keyword in title_lower:
            return "medium"
    return "low"

def _md_sections(text: str) -> List[Tuple[str, str, int]]:
    # Very simple section splitter by Markdown headings
    # Returns: (title, body, heading_level)
    parts = re.split(r"\n(?=#+\s)", text)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        lines = p.splitlines()
        if lines and lines[0].startswith("#"):
            heading_line = lines[0]
            heading_level = len(heading_line) - len(heading_line.lstrip("#"))
            title = heading_line.lstrip("# ").strip()
        else:
            heading_level = 0
            title = "Body"
        out.append((title, p, heading_level))
    return out or [("Body", text, 0)]

def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    tokens = text.split()
    chunks = []
    i = 0
    while i < len(tokens):
        chunk = tokens[i:i+chunk_size]
        chunks.append(" ".join(chunk))
        if i + chunk_size >= len(tokens): break
        i += chunk_size - overlap
    return chunks

def load_documents(data_dir: str) -> List[Dict]:
    docs = []
    for fname in sorted(os.listdir(data_dir)):
        if not fname.lower().endswith((".md", ".txt")):
            continue
        path = os.path.join(data_dir, fname)
        text = _read_text_file(path)
        for section, body, heading_level in _md_sections(text):
            section_priority = _detect_section_priority(section)
            docs.append({
                "title": fname,
                "section": section,
                "text": body,
                "heading_level": heading_level,
                "section_priority": section_priority
            })
    return docs

def doc_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
