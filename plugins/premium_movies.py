from pyrogram import Client, filters
from pyrogram.types import Message

from info import ADMINS
from database.premium_movies_db import (
    add_premium_movie,
    remove_premium_movie,
    get_premium_movies
)


# Add Premium Movie
@Client.on_message(filters.command("addpm") & filters.user(ADMINS))
async def add_pm(client, message: Message):

    if len(message.command) < 2:
        return await message.reply_text(
            "❌ Use:\n\n"
            "/addpm Movie Name\n\n"
            "Multiple Movies:\n"
            "/addpm Movie 1 | Movie 2 | Movie 3"
        )

    movies_text = message.text.split(None, 1)[1]

    movies = [
        movie.strip()
        for movie in movies_text.split("|")
        if movie.strip()
    ]

    added = []
    already = []

    for movie in movies:
        result = await add_premium_movie(movie)

        if result:
            added.append(movie)
        else:
            already.append(movie)


    text = ""

    if added:
        text += "✅ Added Premium Movies:\n\n"
        for movie in added:
            text += f"🔒 {movie}\n"


    if already:
        text += "\n⚠️ Already Exists:\n\n"
        for movie in already:
            text += f"• {movie}\n"


    await message.reply_text(text)


# Remove Premium Movie
@Client.on_message(filters.command("removepm") & filters.user(ADMINS))
async def remove_pm(client, message: Message):

    if len(message.command) < 2:
        return await message.reply_text(
            "❌ Use:\n/removepm Movie Name"
        )

    movie = message.text.split(None,1)[1]

    result = await remove_premium_movie(movie)

    if result:
        await message.reply_text(
            f"✅ Removed From Premium:\n\n{movie}"
        )
    else:
        await message.reply_text(
            "❌ Movie Not Found."
        )


# Premium Movie List
@Client.on_message(filters.command("pmlist") & filters.user(ADMINS))
async def pm_list(client, message: Message):

    movies = await get_premium_movies()

    if not movies:
        return await message.reply_text(
            "📂 No Premium Movies Added."
        )


    text = "🔒 Premium Movies List\n\n"

    for i, movie in enumerate(movies,1):
        text += f"{i}. {movie.title()}\n"


    text += f"\nTotal: {len(movies)}"

    await message.reply_text(text)
