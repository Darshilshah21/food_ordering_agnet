def test_dashboard_empty(client):
    response = client.get("/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_orders"] == 0
    assert data["total_sales"] == 0.0
    assert data["user_wise"] == []


def test_dashboard_user_wise_breakdown(client):
    menu = client.get("/menu").json()
    ids = {x["name"]: x["id"] for x in menu}

    client.post("/orders", json={
        "items": [{"menu_item_id": ids["Test Burger"], "quantity": 2}],
        "user_id": "user-1",
    })
    client.post("/orders", json={
        "items": [{"menu_item_id": ids["Test Coke"], "quantity": 3}],
        "user_id": "user-2",
    })

    data = client.get("/dashboard/summary").json()
    assert data["total_orders"] == 2
    assert data["total_sales"] == 350.0

    by_user = {x["user_id"]: x for x in data["user_wise"]}
    assert by_user["user-1"]["total"] == 200.0
    assert by_user["user-1"]["items"][0]["name"] == "Test Burger"
    assert by_user["user-1"]["items"][0]["quantity"] == 2
    assert by_user["user-1"]["orders"][0]["total"] == 200.0
    assert by_user["user-1"]["orders"][0]["items"][0]["name"] == "Test Burger"
    assert by_user["user-2"]["total"] == 150.0
    assert by_user["user-2"]["orders"][0]["items"][0]["name"] == "Test Coke"
