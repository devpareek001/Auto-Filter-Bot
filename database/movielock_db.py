#added by dev _______#
import motor.motor_asyncio
from info import DATABASE_URI, DATABASE_NAME

_client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URI)
_db = _client[DATABASE_NAME]
locked_movies_col = _db.locked_movies


async def lock_movie(movie_name: str) -> bool:
    key = movie_name.strip().lower()
    existing = await locked_movies_col.find_one({"key": key})
    if existing:
        return False
    await locked_movies_col.insert_one({"key": key, "name": movie_name.strip()})
    return True


async def unlock_movie(movie_name: str) -> bool:
    key = movie_name.strip().lower()
    result = await locked_movies_col.delete_one({"key": key})
    return result.deleted_count > 0


async def get_locked_movies() -> list:
    movies = []
    cursor = locked_movies_col.find({})
    async for doc in cursor:
        movies.append(doc.get("name", doc.get("key", "")))
    return movies


async def is_locked_movie(file_name: str) -> bool:
    if not file_name:
        return False
    name_lower = file_name.lower()
    cursor = locked_movies_col.find({})
    async for doc in cursor:
        key = doc.get("key", "")
        if key and key in name_lower:
            return True
    return False
