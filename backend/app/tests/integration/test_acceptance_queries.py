import pytest

@pytest.mark.parametrize(
    "query,required_docs",
    [
        ("Can a customer return a damaged blender after 20 days?", ["Returns_and_Refunds.md", "Warranty_Policy.md"]),
        ("What’s the shipping SLA to East Malaysia for bulky items?", ["Delivery_and_Shipping.md"]),
    ],
)
def test_acceptance_queries_have_required_citation(client, query, required_docs):
    client.post("/api/ingest")
    resp = client.post("/api/ask", json={"query": query, "k": 4})
    titles = [c["title"] for c in resp.json()["citations"]]
    for doc in required_docs:
        assert doc in titles