from app.rag import _hash_to_uuid, build_chunks_from_docs

def test_hash_to_uuid_truncates():
    hex_hash = "a" * 64
    out = _hash_to_uuid(hex_hash)
    assert out == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

def test_hash_to_uuid_pads_short_value():
    hex_hash = "123"
    out = _hash_to_uuid(hex_hash)
    assert out == "12300000-0000-0000-0000-000000000000"

def test_build_chunks_from_docs_preserves_titles():
    docs = [
        {"title": "Doc1", "section": "Intro", "text": "a b c d"},
        {"title": "Doc2", "section": "Body", "text": "e f g"},
    ]
    chunks = build_chunks_from_docs(docs, chunk_size=2, overlap=0)
    assert chunks[0]["title"] == "Doc1"
    assert chunks[0]["text"] == "a b"
    assert chunks[-1]["title"] == "Doc2"

def test_build_chunks_from_docs_preserves_metadata():
    """Test that metadata (heading_level, section_priority) is preserved in chunks"""
    docs = [
        {
            "title": "Policy.md",
            "section": "SLA",
            "text": "West Malaysia: 2-4 business days",
            "heading_level": 2,
            "section_priority": "high"
        },
        {
            "title": "Guide.md",
            "section": "Introduction",
            "text": "Welcome to the guide",
            "heading_level": 1,
            "section_priority": "low"
        },
    ]
    chunks = build_chunks_from_docs(docs, chunk_size=10, overlap=0)
    
    # Check that metadata is preserved
    assert chunks[0]["heading_level"] == 2
    assert chunks[0]["section_priority"] == "high"
    assert chunks[1]["heading_level"] == 1
    assert chunks[1]["section_priority"] == "low"