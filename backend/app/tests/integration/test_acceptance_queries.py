import pytest

@pytest.mark.parametrize(
    "query,required_docs",
    [
        ("Can a customer return a damaged blender after 20 days?", ["Returns_and_Refunds.md", "Warranty_Policy.md"]),
        ("What's the shipping SLA to East Malaysia for bulky items?", ["Delivery_and_Shipping.md"]),
    ],
)
def test_acceptance_queries_have_required_citation(client, query, required_docs):
    client.post("/api/ingest")
    resp = client.post("/api/ask", json={"query": query, "k": 4})
    data = resp.json()

    # Check document presence
    titles = [c["title"] for c in data["citations"]]
    for doc in required_docs:
        assert doc in titles

    # For shipping query, also check content
    if "bulky" in query.lower() and "shipping" in query.lower():
        answer_has_bulky = "bulky" in data["answer"].lower()
        chunks_have_bulky = any("bulky" in c.get("text", "").lower() for c in data.get("chunks", []))
        
        assert answer_has_bulky or chunks_have_bulky, \
            f"Shipping query must mention 'bulky' in answer or chunks. Answer: {data['answer'][:100]}... Chunks: {[c.get('title') for c in data.get('chunks', [])]}"