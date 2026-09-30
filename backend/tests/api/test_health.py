def test_health(client):
    """Testa l'endpoint health."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"stato": "ok"}
