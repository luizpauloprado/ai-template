from httpx import AsyncClient


async def test_items_crud_flow(client: AsyncClient) -> None:
    created = await client.post("/items", json={"details": {"name": "first"}})
    assert created.status_code == 201
    item = created.json()
    assert item["id"] == 1
    assert item["details"] == {"name": "first"}
    assert "updated_at" in item

    fetched = await client.get(f"/items/{item['id']}")
    assert fetched.json() == item

    updated = await client.put(f"/items/{item['id']}", json={"details": {"name": "second"}})
    assert updated.status_code == 200
    assert updated.json()["details"] == {"name": "second"}

    listed = await client.get("/items")
    assert [i["id"] for i in listed.json()] == [item["id"]]

    deleted = await client.delete(f"/items/{item['id']}")
    assert deleted.status_code == 204
    assert (await client.get(f"/items/{item['id']}")).status_code == 404


async def test_items_pagination(client: AsyncClient) -> None:
    for n in range(3):
        await client.post("/items", json={"details": {"n": n}})

    response = await client.get("/items", params={"limit": 1, "offset": 1})

    assert [i["details"]["n"] for i in response.json()] == [1]


async def test_items_not_found(client: AsyncClient) -> None:
    assert (await client.get("/items/42")).status_code == 404
    assert (await client.put("/items/42", json={"details": {}})).status_code == 404
    assert (await client.delete("/items/42")).status_code == 404


async def test_items_invalid_payload_returns_422(client: AsyncClient) -> None:
    response = await client.post("/items", json={"details": "not an object"})

    assert response.status_code == 422
