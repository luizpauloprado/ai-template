from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from app.dependencies import (
    get_delete_item,
    get_get_item,
    get_insert_item,
    get_list_items,
    get_update_item,
)
from app.domain.models import Item
from app.domain.ports import DeleteItem, GetItem, InsertItem, ListItems, UpdateItem
from app.services import items_service
from app.wires.inbound.items import ItemIn
from app.wires.outbound.items import ItemOut, to_item_out

router = APIRouter(prefix="/items", tags=["items"])

ItemId = Annotated[int, Path(ge=1)]


def ensure_found(item: Item | None) -> Item:
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "item not found")
    return item


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
async def create_item(
    wire_in: ItemIn, insert_item: Annotated[InsertItem, Depends(get_insert_item)]
) -> ItemOut:
    item = await items_service.create_item(wire_in.details, insert_item)
    return to_item_out(item)


@router.get("", response_model=list[ItemOut])
async def list_items(
    list_all: Annotated[ListItems, Depends(get_list_items)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ItemOut]:
    items = await items_service.list_items(limit, offset, list_all)
    return [to_item_out(item) for item in items]


@router.get("/{item_id}", response_model=ItemOut)
async def get_item(item_id: ItemId, get: Annotated[GetItem, Depends(get_get_item)]) -> ItemOut:
    item = await items_service.get_item(item_id, get)
    return to_item_out(ensure_found(item))


@router.put("/{item_id}", response_model=ItemOut)
async def update_item(
    item_id: ItemId, wire_in: ItemIn, update: Annotated[UpdateItem, Depends(get_update_item)]
) -> ItemOut:
    item = await items_service.update_item(item_id, wire_in.details, update)
    return to_item_out(ensure_found(item))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: ItemId, delete: Annotated[DeleteItem, Depends(get_delete_item)]
) -> Response:
    if not await items_service.delete_item(item_id, delete):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "item not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
