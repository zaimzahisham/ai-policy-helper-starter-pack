from app.ingest import chunk_text

def test_chunk_text_with_overlap():
    text = "one two three four five six seven eight"
    chunks = chunk_text(text, chunk_size=3, overlap=1)
    assert chunks == [
        "one two three",
        "three four five",
        "five six seven",
        "seven eight",
    ]