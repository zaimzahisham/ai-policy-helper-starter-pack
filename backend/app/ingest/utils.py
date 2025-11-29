"""Utility functions for ingestion."""
import hashlib


def doc_hash(text: str) -> str:
    """Compute SHA-256 hash of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

