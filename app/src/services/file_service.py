from pathlib import Path

import aiofiles
from fastapi import UploadFile

from ..db.models import User


async def write_to_disk(user: User, file: UploadFile, static_path: str) -> str:

    path = Path(f"images/{user.id}")
    absolute_path = Path(static_path).absolute() / path
    absolute_path.mkdir(exist_ok=True, parents=True)
    if file.filename:
        file_path = path / file.filename
    else:
        file_path = path / "UPLOAD"
    content = await file.read()
    async with aiofiles.open(static_path / file_path, mode="wb") as f:
        await f.write(content)
    return str(file_path)
