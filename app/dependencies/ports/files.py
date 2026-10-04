from typing import Annotated

from fastapi import Depends

from app.adapters.fs import file_reader
from app.domain.ports import ReadFile


def get_read_file() -> ReadFile:
    return file_reader.read_bytes


ReadFileDep = Annotated[ReadFile, Depends(get_read_file)]
