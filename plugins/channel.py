import re
import io
import math
import random
import string
import base64
import aiohttp
import asyncio
import hashlib
import requests
from info import *
from utils import *
from logging_helper import LOGGER
from typing import Optional, Dict, Any
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from database.ia_filterdb import save_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


CAPTION_LANGUAGES = ["Bhojpuri", "Hindi", "Bengali", "Tamil", "English", "Bangla", "Telugu", "Malayalam", "Kannada", "Marathi", "Punjabi", "Bengoli", "Gujrati", "Korean", "Gujarati", "Spanish", "French", "German", "Chinese", "Arabic", "Portuguese", "Russian", "Japanese", "Odia", "Assamese", "Urdu"]

DEFAULT_IMAGE_URL = "https://te.legra.ph/file/88d845b4f8a024a71465d.jpg"

DEV_UPDATE_CAPTION = """
<blockquote>🎬 𝗠𝗢𝗩𝗜𝗘 𝗨𝗣𝗗𝗔𝗧𝗘 🎥</blockquote>

<b><u>{}</u></b> <code>#{}</code>

<code>━━━━━━━━━━━━━━━━━━</code>
<b>🔈 Audio</b>: {}
<b>📺 Format</b>: {}

<code>━━━━━━━━━━━━━━━━━━</code>
<b>🎭 Director</b>: {}
<b>📅 Release</b>: {}
<b>⭐ IMDb</b>: {}/10 (<code>{}</code> votes)
<b>🏷️ Genres</b>: {}
<code>━━━━━━━━━━━━━━━━━━</code>
"""

notified_movies = set()
user_reactions = {}
reaction_counts = {}

media_filter = filters.document | filters.video | filters.audio
media_process_lock = asyncio.Lock()

@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    """Media Handler"""
    for file_type in ("document", "video", "audio"):
        media = getattr(message, file_type, None)
        if media is not None:
            break
    else:
        return
    media.file_type = file_type
    media.caption = message.caption

    async with media_process_lock:
        try:
            success, dev = await save_file(media)
            if success and dev == 1 and await get_status(bot.me.id):
                await send_movie_update(bot, file_name=media.file_name, caption=media.caption)
        except Exception as e:
            LOGGER.error(f"Error In Movie Update - {e}")
            pass

async def send_movie_update(bot, file_name, caption):
    try:
        file_name = await movie_name_format(file_name)
        caption = await movie_name_format(caption)
        year_match = re.search(r"\b(19|20)\d{2}\b", caption)
        year = year_match.group(0) if year_match else None      
        season_match = re.search(r"(?i)(?:s|season)0*(\d{1,2})", caption) or re.search(r"(?i)(?:s|season)0*(\d{1,2})", file_name)
        if year:
            file_name = file_name[:file_name.find(year) + 4]
        elif season_match:
            season = season_match.group(1)
            file_name = file_name[:file_name.find(season) + 1]
        language = ", ".join([lang for lang in CAPTION_LANGUAGES if lang.lower() in caption.lower()]) or "Multi-Audio"
        if file_name in notified_movies:
            return 
        notified_movies.add(file_name)

        tmdb_data = await fetch_tmdb_data(file_name, year)
        search_movie = file_name.replace(" ", "-")
        unique_id = generate_unique_id(search_movie)
        reaction_counts[unique_id] = {"❤️": 0, "👍": 0, "👎": 0, "🔥": 0}
        user_reactions[unique_id] = {}

        if tmdb_data:
            title = tmdb_data["title"]
            kind = tmdb_data["kind"]
            director = tmdb_data["director"] or "N/A"
            release_date = tmdb_data["release_date"] or "TBA"
            vote_average = tmdb_data["vote_average"]
            vote_count = tmdb_data["vote_count"]
            genres = ", ".join(tmdb_data["genres"][:3]) or "N/A"
        else:
            imdb_data = await get_imdb_details(file_name)
            title = imdb_data.get("title", file_name)
            kind = (imdb_data.get("kind", "") or "MOVIE").strip().upper().replace(" ", "_")
            director = "N/A"
            release_date = "TBA"
            vote_average = 0
            vote_count = 0
            genres = "N/A"

        audio_format = "MKV" if "mkv" in file_name.lower() else "MP4"
        full_caption = DEV_UPDATE_CAPTION.format(
            escape_html(title),
            kind,
            escape_html(language),
            audio_format,
            escape_html(director),
            escape_html(release_date),
            vote_average,
            vote_count,
            escape_html(genres)
        )
        buttons = [[
            InlineKeyboardButton(f"❤️ {reaction_counts[unique_id]['❤️']}", callback_data=f"r_{unique_id}_{search_movie}_heart"),                
            InlineKeyboardButton(f"👍 {reaction_counts[unique_id]['👍']}", callback_data=f"r_{unique_id}_{search_movie}_like"),
            InlineKeyboardButton(f"👎 {reaction_counts[unique_id]['👎']}", callback_data=f"r_{unique_id}_{search_movie}_dislike"),
            InlineKeyboardButton(f"🔥 {reaction_counts[unique_id]['🔥']}", callback_data=f"r_{unique_id}_{search_movie}_fire")
        ],[
            InlineKeyboardButton('Get File', url=f'https://telegram.me/{temp.U_NAME}?start=getfile-{search_movie}')
        ]]
        await send_with_visual(bot, full_caption, tmdb_data, title, year, InlineKeyboardMarkup(buttons))
    except Exception as e:
        LOGGER.error(f"Error in send_movie_update: {e}")

def escape_html(text) -> str:
    if not text:
        return ""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

async def send_with_visual(bot, caption: str, tmdb_data: Optional[Dict], title: str, year, reply_markup):
    """
    Mirrors the friend's send_with_visual flow:
    get_best_visual() -> a plain image URL (16:9 TMDb backdrop, if we have one)
    -> download it here and send.
    If TMDb had nothing at all, falls back to the 2:3 custom poster API,
    and only if THAT also fails, uses the generic default banner image.
    """
    try:
        visual_url = get_best_visual(tmdb_data)

        if visual_url:
            async with aiohttp.ClientSession() as session:
                async with session.get(visual_url, timeout=aiohttp.ClientTimeout(total=20)) as img_resp:
                    if img_resp.status == 200:
                        img_bytes = await img_resp.read()
                        photo_file = io.BytesIO(img_bytes)
                        photo_file.name = await generate_random_filename()
                        await bot.send_photo(
                            chat_id=MOVIE_UPDATE_CHANNEL,
                            photo=photo_file,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                            reply_markup=reply_markup
                        )
                        return
                    LOGGER.error(f"Visual URL download failed for '{title}': HTTP {img_resp.status}")

        # TMDb had no 16:9 backdrop at all - try the 2:3 custom poster API.
        poster_bytes = await fetch_custom_poster(title, year)
        if poster_bytes:
            photo_file = io.BytesIO(poster_bytes)
            photo_file.name = await generate_random_filename()
            await bot.send_photo(
                chat_id=MOVIE_UPDATE_CHANNEL,
                photo=photo_file,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            return

        # Nothing worked at all - generic default banner so the update still goes out.
        await bot.send_photo(
            chat_id=MOVIE_UPDATE_CHANNEL,
            photo=DEFAULT_IMAGE_URL,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    except Exception as e:
        LOGGER.error(f"Visual Send Error: {e}")

def get_best_visual(tmdb_data: Optional[Dict]) -> Optional[str]:
    """Returns the full 16:9 TMDb backdrop image URL, or None if we have no TMDb data."""
    if not tmdb_data:
        return None
    backdrop_path = tmdb_data.get("backdrop_path")
    if not backdrop_path:
        return None
    return f"https://image.tmdb.org/t/p/original{backdrop_path}"

@Client.on_callback_query(filters.regex(r"^r_"))
async def reaction_handler(client, query):
    try:
        data = query.data.split("_")
        if len(data) != 4:
            return        
        unique_id = data[1]
        search_movie = data[2]
        new_reaction = data[3]
        user_id = query.from_user.id
        emoji_map = {"heart": "❤️", "like": "👍", "dislike": "👎", "fire": "🔥"}
        if new_reaction not in emoji_map:
            return
        new_emoji = emoji_map[new_reaction]       
        if unique_id not in reaction_counts:
            return
        if user_id in user_reactions[unique_id]:
            old_emoji = user_reactions[unique_id][user_id]
            if old_emoji == new_emoji:
                return 
            else:
                reaction_counts[unique_id][old_emoji] -= 1
        user_reactions[unique_id][user_id] = new_emoji
        reaction_counts[unique_id][new_emoji] += 1
        updated_buttons = [[
            InlineKeyboardButton(f"❤️ {reaction_counts[unique_id]['❤️']}", callback_data=f"r_{unique_id}_{search_movie}_heart"),                
            InlineKeyboardButton(f"👍 {reaction_counts[unique_id]['👍']}", callback_data=f"r_{unique_id}_{search_movie}_like"),
            InlineKeyboardButton(f"👎 {reaction_counts[unique_id]['👎']}", callback_data=f"r_{unique_id}_{search_movie}_dislike"),
            InlineKeyboardButton(f"🔥 {reaction_counts[unique_id]['🔥']}", callback_data=f"r_{unique_id}_{search_movie}_fire")
        ],[
            InlineKeyboardButton('Get File', url=f'https://telegram.me/{temp.U_NAME}?start=getfile-{search_movie}')
        ]]
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(updated_buttons))
    except Exception as e:
        LOGGER.error("Reaction error:", e)
        
async def get_imdb_details(name):
    try:
        formatted_name = await movie_name_format(name)
        imdb = await get_poster(formatted_name)
        if not imdb:
            return {}
        return {
            "title": imdb.get("title", formatted_name),
            "kind": imdb.get("kind", "Movie"),
            "year": imdb.get("year"),
            "url" : imdb.get("url")
        }
    except Exception as e:
        LOGGER.error(f"IMDB fetch error: {e}")
        return {}

async def fetch_tmdb_data(title: str, year: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Searches TMDb for this title (movie first, then TV series) and returns a dict with
    everything needed for the update caption: title, kind, release_date, rating,
    genres, director - plus backdrop_path (a TMDb file path string, NOT downloaded
    bytes - get_best_visual() turns this into the full image URL).
    Returns None if TMDb has no match at all for this title.
    """
    if not TMDB_API_KEY:
        LOGGER.error(f"TMDB_API_KEY is empty/not set - skipping TMDb lookup for '{title}'")
        return None
    try:
        async with aiohttp.ClientSession() as session:
            result = None
            matched_endpoint = None
            # Try: movie+year -> movie without year (in case the extracted year was wrong) -> tv show.
            attempts = [("movie", True), ("movie", False), ("tv", False)]
            for endpoint, use_year in attempts:
                search_params = {"api_key": TMDB_API_KEY, "query": title.strip()}
                if use_year and year is not None:
                    search_params["year"] = str(year)
                async with session.get(
                    f"https://api.themoviedb.org/3/search/{endpoint}",
                    params=search_params,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status != 200:
                        LOGGER.error(f"TMDb search ({endpoint}, year={use_year}) failed for '{title}': HTTP {resp.status}")
                        continue
                    data = await resp.json(content_type=None)
                    results = data.get("results") or []
                    if results:
                        result = results[0]
                        matched_endpoint = endpoint
                        break
                    else:
                        LOGGER.info(f"TMDb search ({endpoint}, year={use_year}) found no results for '{title}'")

            if not result or not matched_endpoint:
                LOGGER.info(f"TMDb has no match at all for '{title}' - falling back to IMDb + custom poster API")
                return None

            tmdb_id = result.get("id")

            # One combined call: full details + cast/crew (for director) + all images (for backdrop).
            async with session.get(
                f"https://api.themoviedb.org/3/{matched_endpoint}/{tmdb_id}",
                params={"api_key": TMDB_API_KEY, "append_to_response": "credits,images"},
                timeout=aiohttp.ClientTimeout(total=15)
            ) as detail_resp:
                if detail_resp.status != 200:
                    LOGGER.error(f"TMDb details fetch failed for '{title}' (id={tmdb_id}): HTTP {detail_resp.status}")
                    return None
                details = await detail_resp.json(content_type=None)

            movie_title = details.get("title") or details.get("name") or title
            kind = "MOVIE" if matched_endpoint == "movie" else "TV_SERIES"
            release_date = details.get("release_date") or details.get("first_air_date") or ""
            vote_average = round(details.get("vote_average", 0) or 0, 1)
            vote_count = details.get("vote_count", 0) or 0
            genres = [g.get("name") for g in (details.get("genres") or []) if g.get("name")]

            director = ""
            if matched_endpoint == "movie":
                crew = (details.get("credits") or {}).get("crew") or []
                directors = [c.get("name") for c in crew if c.get("job") == "Director"]
                director = ", ".join(directors[:2])
            else:
                creators = details.get("created_by") or []
                director = ", ".join([c.get("name") for c in creators if c.get("name")][:2])

            # Pick the best-rated 16:9 backdrop from the FULL image list (much more
            # reliable than the single 'backdrop_path' field, which is often empty).
            backdrop_path = None
            backdrops = (details.get("images") or {}).get("backdrops") or []
            if backdrops:
                backdrops.sort(key=lambda b: b.get("vote_average", 0), reverse=True)
                backdrop_path = backdrops[0].get("file_path")
            if not backdrop_path:
                backdrop_path = details.get("backdrop_path")

            if not backdrop_path:
                LOGGER.info(f"TMDb matched '{title}' but has no 16:9 backdrop at all")

            return {
                "title": movie_title,
                "kind": kind,
                "release_date": release_date,
                "vote_average": vote_average,
                "vote_count": vote_count,
                "genres": genres,
                "director": director,
                "backdrop_path": backdrop_path,
            }
    except aiohttp.ClientError as e:
        LOGGER.error(f"TMDb network error for '{title}': {str(e)}")
    except asyncio.TimeoutError:
        LOGGER.error(f"TMDb request timed out for '{title}'")
    except Exception as e:
        LOGGER.error(f"TMDb unexpected error for '{title}': {str(e)}")
    return None


async def fetch_custom_poster(title: str, year: Optional[str] = None) -> Optional[bytes]:
    base_url = "https://black-bonus-46d1.parikgovind45.workers.dev/api/v2/poster"
    params = {"title": title.strip(), "type": "poster"}
    if year is not None:
        params["year"] = str(year)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "*/*",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                base_url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as response:
                content_type = (response.headers.get("Content-Type") or "").lower()

                if response.status != 200:
                    response_text = await response.text()
                    LOGGER.error(f"Poster API error for '{title}': HTTP {response.status} - {response_text[:300]}")
                    return None

                # Case 1: API directly returns the image bytes.
                if content_type.startswith("image/"):
                    return await response.read()

                # Case 2: API returns JSON with a poster URL / base64 image inside it.
                if "application/json" in content_type or content_type == "":
                    try:
                        data = await response.json(content_type=None)
                    except Exception:
                        raw = await response.read()
                        LOGGER.error(f"Poster API returned unreadable JSON for '{title}': {raw[:200]}")
                        return None

                    if isinstance(data, dict):
                        poster_value = (
                            data.get("poster") or data.get("image") or data.get("url")
                            or data.get("poster_url") or data.get("data") or data.get("result")
                        )
                    else:
                        poster_value = None

                    if not poster_value:
                        LOGGER.error(f"Poster API JSON had no usable image field for '{title}': {str(data)[:300]}")
                        return None

                    # Sub-case: JSON gave us a base64-encoded image instead of a URL.
                    if isinstance(poster_value, str) and poster_value.strip().startswith("data:image"):
                        try:
                            b64_part = poster_value.split(",", 1)[1]
                            return base64.b64decode(b64_part)
                        except Exception as e:
                            LOGGER.error(f"Failed decoding base64 poster for '{title}': {e}")
                            return None

                    # Sub-case: JSON gave us a plain image URL - fetch the actual image.
                    if isinstance(poster_value, str) and poster_value.startswith("http"):
                        async with session.get(poster_value, timeout=aiohttp.ClientTimeout(total=20)) as img_resp:
                            if img_resp.status == 200:
                                return await img_resp.read()
                            LOGGER.error(f"Failed downloading poster image URL for '{title}': HTTP {img_resp.status}")
                            return None

                    LOGGER.error(f"Poster API JSON field wasn't a usable URL/base64 for '{title}': {str(poster_value)[:200]}")
                    return None

                # Fallback: unknown content-type, just try treating it as raw image bytes.
                raw = await response.read()
                if raw:
                    return raw
                return None

    except aiohttp.ClientError as e:
        LOGGER.error(f"Network error occurred while fetching poster for '{title}': {str(e)}")
    except asyncio.TimeoutError:
        LOGGER.error(f"Poster API request timed out after 20 seconds for '{title}'")
    except Exception as e:
        LOGGER.error(f"Unexpected error fetching poster for '{title}': {str(e)}")
    return None


def generate_unique_id(movie_name):
    return hashlib.md5(movie_name.encode('utf-8')).hexdigest()[:5]

async def get_qualities(text):
    qualities = ["ORG", "org", "hdcam", "HDCAM", "HQ", "hq", "HDRip", "hdrip", 
                 "camrip", "WEB-DL", "CAMRip", "hdtc", "predvd", "DVDscr", "dvdscr", 
                 "dvdrip", "HDTC", "dvdscreen", "HDTS", "hdts"]
    return ", ".join([q for q in qualities if q.lower() in text.lower()])


async def get_pixels(caption):
    pixels = ["480p", "480p HEVC", "720p", "720p HEVC", "1080p", "1080p HEVC", "2160p" "2K", "4K"]
    return ", ".join([p for p in pixels if p.lower() in caption.lower()])


async def movie_name_format(file_name):
  clean_filename = re.sub(r'http\S+', '', re.sub(r'@\w+|#\w+', '', file_name).replace('_', ' ').replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace('{', '').replace('}', '').replace('.', ' ').replace('@', '').replace(':', '').replace(';', '').replace("'", '').replace('-', '').replace('!', '')).strip()
  return clean_filename


async def generate_random_filename(extension=".jpg"):
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    sin_value = abs(math.sin(int(timestamp[-5:]))) 
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))   
    filename = f"dev_{int(sin_value*10000)}_{random_part}{extension}"
    return filename

