from app.services import items_service
from tests.fakes import make_fake_item_table


async def test_create_and_get() -> None:
    table = make_fake_item_table()

    created = await items_service.create_item({"name": "a"}, table["insert"])
    found = await items_service.get_item(created.id, table["get"])

    assert found == created


async def test_list_respects_limit_and_offset() -> None:
    table = make_fake_item_table()
    for i in range(5):
        await items_service.create_item({"n": i}, table["insert"])

    page = await items_service.list_items(2, 1, table["list"])

    assert [item.details["n"] for item in page] == [1, 2]


async def test_update_missing_returns_none() -> None:
    table = make_fake_item_table()

    assert await items_service.update_item(99, {}, table["update"]) is None


async def test_delete() -> None:
    table = make_fake_item_table()
    created = await items_service.create_item({}, table["insert"])

    assert await items_service.delete_item(created.id, table["delete"]) is True
    assert await items_service.delete_item(created.id, table["delete"]) is False
