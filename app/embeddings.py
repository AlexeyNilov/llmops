import aiofiles


async def read_text(filepath: str) -> str:
    async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
        return await f.read()
