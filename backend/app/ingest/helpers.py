"""Helper functions for document parsing and chunking."""
import re
from typing import List, Tuple


def _read_text_file(path: str) -> str:
    """Read text file with UTF-8 encoding, ignoring errors."""
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
    """
    Very simple section splitter by Markdown headings.
    Returns: (title, body, heading_level)
    """
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
    """
    Split text into chunks of specified size with overlap.
    
    Args:
        text: Text to chunk
        chunk_size: Number of words per chunk
        overlap: Number of words to overlap between chunks
    
    Returns:
        List of chunk strings
    """
    tokens = text.split()
    chunks = []
    i = 0
    while i < len(tokens):
        chunk = tokens[i:i+chunk_size]
        chunks.append(" ".join(chunk))
        if i + chunk_size >= len(tokens):
            break
        i += chunk_size - overlap
    return chunks

