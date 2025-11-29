"""Core ingestion functions: document loading and chunk building."""
import logging
import os
from typing import List, Dict
from .helpers import _read_text_file, _md_sections, _detect_section_priority, chunk_text

logger = logging.getLogger(__name__)


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
    logger.info(f"Loading documents from {data_dir}")
    try:
        for fname in sorted(os.listdir(data_dir)):
            # Treat Internal_SOP_Agent_Guide.md as agent instructions, not user-facing policy:
            # it is loaded separately in the RAG engine and injected into the LLM prompt.
            # We explicitly exclude it from normal retrieval/citations here.
            if fname == "Internal_SOP_Agent_Guide.md":
                logger.debug(f"Skipping {fname} (agent guide, not policy)")
                continue
            if not fname.lower().endswith((".md", ".txt")):
                logger.debug(f"Skipping {fname} (not .md or .txt)")
                continue
            path = os.path.join(data_dir, fname)
            try:
                text = _read_text_file(path)
                sections = list(_md_sections(text))
                logger.debug(f"Loaded {fname}: {len(sections)} sections")
                for section, body, heading_level in sections:
                    section_priority = _detect_section_priority(section)
                    docs.append({
                        "title": fname,
                        "section": section,
                        "text": body,
                        "heading_level": heading_level,
                        "section_priority": section_priority
                    })
            except Exception as e:
                logger.warning(f"Error loading file {fname}: {str(e)}", exc_info=True)
                continue
        logger.info(f"Successfully loaded {len(docs)} document sections from {len(set(d['title'] for d in docs))} files")
    except FileNotFoundError:
        logger.error(f"Data directory not found: {data_dir}")
        raise
    except Exception as e:
        logger.error(f"Error loading documents from {data_dir}: {str(e)}", exc_info=True)
        raise
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

