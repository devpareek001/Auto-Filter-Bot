import motor.motor_asyncio
from info import DATABASE_URI, DATABASE_NAME

_client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URI)
_db = _client[DATABASE_NAME]
locked_movies_col = _db.locked_movies

# ---- In-memory cache ----
# Avoids hitting MongoDB on every single file delivery (which was slowing
# things down). The cache is refreshed whenever a movie is locked/unlocked,
# and also loaded once automatically the first time it's needed.
_cache = None  # list of {"key": ..., "name": ...} once loaded


async def _load_cache():
    global _cache
    _cache = []
    cursor = locked_movies_col.find({})
    async for doc in cursor:
        _cache.append(doc)


async def lock_movie(movie_name: str) -> bool:
    key = movie_name.strip().lower()
    existing = await locked_movies_col.find_one({"key": key})
    if existing:
        return False
    await locked_movies_col.insert_one({"key": key, "name": movie_name.strip()})
    await _load_cache()  # refresh cache
    return True


async def unlock_movie(movie_name: str) -> bool:
    key = movie_name.strip().lower()
    result = await locked_movies_col.delete_one({"key": key})
    if result.deleted_count > 0:
        await _load_cache()  # refresh cache
        return True
    return False


async def get_locked_movies() -> list:
    global _cache
    if _cache is None:
        await _load_cache()
    return [doc.get("name", doc.get("key", "")) for doc in _cache]


async def is_locked_movie(file_name: str) -> bool:
    global _cache
    if not file_name:
        return False
    if _cache is None:
        await _load_cache()
    if not _cache:
        return False
    name_lower = file_name.lower()
    for doc in _cache:
        key = doc.get("key", "")
        if key and key in name_lower:
            return True
    return False
