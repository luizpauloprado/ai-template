from functools import partial
from typing import Annotated

from fastapi import Depends

from app.adapters.db import item_repository
from app.dependencies.resources import PoolDep
from app.domain.ports import DeleteItem, GetItem, InsertItem, ListItems, UpdateItem


def get_insert_item(pool: PoolDep) -> InsertItem:
    return partial(item_repository.insert_item, pool)


def get_get_item(pool: PoolDep) -> GetItem:
    return partial(item_repository.get_item, pool)


def get_list_items(pool: PoolDep) -> ListItems:
    return partial(item_repository.list_items, pool)


def get_update_item(pool: PoolDep) -> UpdateItem:
    return partial(item_repository.update_item, pool)


def get_delete_item(pool: PoolDep) -> DeleteItem:
    return partial(item_repository.delete_item, pool)


InsertItemDep = Annotated[InsertItem, Depends(get_insert_item)]
GetItemDep = Annotated[GetItem, Depends(get_get_item)]
ListItemsDep = Annotated[ListItems, Depends(get_list_items)]
UpdateItemDep = Annotated[UpdateItem, Depends(get_update_item)]
DeleteItemDep = Annotated[DeleteItem, Depends(get_delete_item)]
