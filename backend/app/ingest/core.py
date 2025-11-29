"""Core ingestion functions: document loading and chunk building."""
import os
from typing import List, Dict
from .helpers import _read_text_file, _md_sections, _detect_section_priority, chunk_text


def load_documents(data_dir: str) -> List[Dict]:
    """
    Load and parse documents from a directory.
    
    Excludes Internal_SOP_Agent_Guide.md (treated as agent instructions, not policy).
    Each document section is parsed with metadata (heading_level, section_priority).
    
    Args:
        data_dir: Directory containing .md and .txt files
    
    Returns:
        List of document dictionaries with title, section, text, heading_level, section_priority
    """
    docs = []
    for fname in sorted(os.listdir(data_dir)):
        # Treat Internal_SOP_Agent_Guide.md as agent instructions, not user-facing policy:
        # it is loaded separately in the RAG engine and injected into the LLM prompt.
        # We explicitly exclude it from normal retrieval/citations here.
        if fname == "Internal_SOP_Agent_Guide.md":
            continue
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


def build_chunks_from_docs(docs: List[Dict], chunk_size: int, overlap: int) -> List[Dict]:
    """
    Build chunks from documents, preserving metadata.
    
    Takes document sections and splits them into smaller chunks while preserving
    metadata (title, section, heading_level, section_priority).
    
    Args:
        docs: List of document dictionaries (from load_documents)
        chunk_size: Number of words per chunk
        overlap: Number of words to overlap between chunks
    
    Returns:
        List of chunk dictionaries with title, section, text, heading_level, section_priority
    """
    out = []
    for d in docs:
        for ch in chunk_text(d["text"], chunk_size, overlap):
            out.append({
                "title": d["title"],
                "section": d["section"],
                "text": ch,
                "heading_level": d.get("heading_level", 0),
                "section_priority": d.get("section_priority", "low")
            })
    return out

