from pathlib import Path

import pytest

from app.adapters.fs.file_reader import read_bytes


async def test_read_bytes_returns_file_content(tmp_path: Path) -> None:
    path = tmp_path / "doc.pdf"
    path.write_bytes(b"%PDF-1.4")

    assert await read_bytes(path) == b"%PDF-1.4"


async def test_read_bytes_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        await read_bytes(tmp_path / "missing.pdf")
