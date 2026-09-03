def test_create_multi_item_order(client):
    menu = client.get("/menu").json()
    ids = {x["name"]: x["id"] for x in menu}

    response = client.post("/orders", json={
        "items": [
            {"menu_item_id": ids["Test Burger"], "quantity": 2},
            {"menu_item_id": ids["Test Coke"], "quantity": 3},
        ],
        "user_id": "user-1",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["total_amount"] == "350.00"
    assert data["user_id"] == "user-1"
    assert len(data["items"]) == 2


def test_order_not_found(client):
    response = client.get("/orders/9999")
    assert response.status_code == 404
