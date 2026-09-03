def test_legacy_slug_is_resolved(client):
    response = client.post("/orders", json={
        "items": [{"menu_item_id": "test-burger", "quantity": 2}],
        "user_id": "user-slug-test",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["name"] == "Test Burger"
    assert data["items"][0]["quantity"] == 2


def test_invalid_item_does_not_create_order(client):
    response = client.post("/orders", json={
        "items": [{"menu_item_id": "definitely-not-on-menu", "quantity": 1}]
    })
    assert response.status_code == 400

    dashboard = client.get("/dashboard/summary").json()
    assert dashboard["total_orders"] == 0
