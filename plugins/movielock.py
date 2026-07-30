from pyrogram import Client, filters
from pyrogram.types import Message

from info import ADMINS
from database.movielock_db import (
    lock_movie,
    unlock_movie,
    get_locked_movies
)


@Client.on_message(filters.command("lockmovie") & filters.user(ADMINS))
async def lock_movie_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ Use:\n\n/lockmovie Movie Name\n\nMultiple:\n/lockmovie Movie 1 | Movie 2"
        )

    movies_text = message.text.split(None, 1)[1]
    movies = [m.strip() for m in movies_text.split("|") if m.strip()]

    added, already = [], []
    for movie in movies:
        result = await lock_movie(movie)
        (added if result else already).append(movie)

    text = ""
    if added:
        text += "✅ Locked (Premium Only):\n\n"
        for movie in added:
            text += f"🔒 {movie}\n"
    if already:
        text += "\n⚠️ Already Locked:\n\n"
        for movie in already:
            text += f"• {movie}\n"

    await message.reply_text(text)


@Client.on_message(filters.command("unlockmovie") & filters.user(ADMINS))
async def unlock_movie_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Use:\n/unlockmovie Movie Name")

    movie = message.text.split(None, 1)[1]
    result = await unlock_movie(movie)

    if result:
        await message.reply_text(f"✅ Unlocked:\n\n{movie}")
    else:
        await message.reply_text("❌ Movie Not Found In Locked List.")


@Client.on_message(filters.command("lockedlist") & filters.user(ADMINS))
async def locked_list_cmd(client, message: Message):
    movies = await get_locked_movies()

    if not movies:
        return await message.reply_text("📂 No Movies Are Locked (Premium Only).")

    text = "🔒 Premium-Only (Locked) Movies\n\n"
    for i, movie in enumerate(movies, 1):
        text += f"{i}. {movie.title()}\n"
    text += f"\nTotal: {len(movies)}"

    await message.reply_text(text)
