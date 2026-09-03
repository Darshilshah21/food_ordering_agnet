def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_menu(client):
    response = client.get("/menu")
    assert response.status_code == 200
    names = {x["name"] for x in response.json()}
    assert "Test Burger" in names
    assert "Test Coke" in names
