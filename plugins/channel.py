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
from typing import Optional
from datetime import datetime
from pyrogram import Client, filters
from database.ia_filterdb import save_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


CAPTION_LANGUAGES = ["Bhojpuri", "Hindi", "Bengali", "Tamil", "English", "Bangla", "Telugu", "Malayalam", "Kannada", "Marathi", "Punjabi", "Bengoli", "Gujrati", "Korean", "Gujarati", "Spanish", "French", "German", "Chinese", "Arabic", "Portuguese", "Russian", "Japanese", "Odia", "Assamese", "Urdu"]

DEV_UPDATE_CAPTION = """𝖭𝖤𝖶 𝖥𝖨𝖫𝖤 𝖠𝖣𝖣𝖤𝖣 ✅

{} #{}
📺 𝖥𝗈𝗋𝗆𝖺𝗍 - {}
🔰 𝖰𝗎𝖺𝗅𝗂𝗍𝗒 - {}
🔈 𝖠𝗎𝖽𝗂𝗈 - {}
🖇️ <a href="{}">𝖨𝖬𝖣𝖡 𝖨𝗇𝖿𝗈</a>
"""

notified_movies = set()
user_reactions = {}
reaction_counts = {}

media_filter = filters.document | filters.video | filters.audio

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
    success, dev = await save_file(media)
    try:  
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
        quality = await get_qualities(caption) or "HDRip"
        pixel = await get_pixels(caption) or "720p"
        language = ", ".join([lang for lang in CAPTION_LANGUAGES if lang.lower() in caption.lower()]) or "Not Idea"
        if file_name in notified_movies:
            return 
        notified_movies.add(file_name)
        imdb_data = await get_imdb_details(file_name)
        title = imdb_data.get("title", file_name)
        imdb_link = imdb_data.get("url", "") if imdb_data else ""
        kind = imdb_data.get("kind", "").strip().upper().replace(" ", "_") if imdb_data else ""
        poster = await fetch_movie_poster(title, year)        
        search_movie = file_name.replace(" ", "-")
        unique_id = generate_unique_id(search_movie)
        reaction_counts[unique_id] = {"❤️": 0, "👍": 0, "👎": 0, "🔥": 0}
        user_reactions[unique_id] = {}        
        full_caption = DEV_UPDATE_CAPTION.format(file_name, kind, quality, pixel, language, imdb_link)
        buttons = [[
            InlineKeyboardButton(f"❤️ {reaction_counts[unique_id]['❤️']}", callback_data=f"r_{unique_id}_{search_movie}_heart"),                
            InlineKeyboardButton(f"👍 {reaction_counts[unique_id]['👍']}", callback_data=f"r_{unique_id}_{search_movie}_like"),
            InlineKeyboardButton(f"👎 {reaction_counts[unique_id]['👎']}", callback_data=f"r_{unique_id}_{search_movie}_dislike"),
            InlineKeyboardButton(f"🔥 {reaction_counts[unique_id]['🔥']}", callback_data=f"r_{unique_id}_{search_movie}_fire")
        ],[
            InlineKeyboardButton('Get File', url=f'https://telegram.me/{temp.U_NAME}?start=getfile-{search_movie}')
        ]]
        if poster:
            photo_file = io.BytesIO(poster)
            photo_file.name = await generate_random_filename()
            await bot.send_photo(chat_id=MOVIE_UPDATE_CHANNEL, photo=photo_file, caption=full_caption, reply_markup=InlineKeyboardMarkup(buttons))    
        else:
            image_url = "https://te.legra.ph/file/88d845b4f8a024a71465d.jpg"   
            await bot.send_photo(chat_id=MOVIE_UPDATE_CHANNEL, photo=image_url, caption=full_caption, reply_markup=InlineKeyboardMarkup(buttons))                
    except Exception as e:
        LOGGER.error(f"Error in send_movie_update: {e}")

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

async def fetch_movie_poster(title: str, year: Optional[int] = None) -> Optional[bytes]:
    """
    Fetches a wide/landscape 'banner' style backdrop image via TMDb (matches the
    castle-scene wide banner format). Falls back to the custom poster API
    (portrait format) if TMDb has nothing for this title.
    """
    banner = await fetch_tmdb_backdrop(title, year)
    if banner:
        return banner
    return await fetch_custom_poster(title, year)


async def fetch_tmdb_backdrop(title: str, year: Optional[int] = None) -> Optional[bytes]:
    if not TMDB_API_KEY:
        return None
    try:
        async with aiohttp.ClientSession() as session:
            result = None
            # Try as a movie first, then as a TV/web series if nothing was found.
            for endpoint in ("movie", "tv"):
                search_params = {"api_key": TMDB_API_KEY, "query": title.strip()}
                if year is not None and endpoint == "movie":
                    search_params["year"] = str(year)
                async with session.get(
                    f"https://api.themoviedb.org/3/search/{endpoint}",
                    params=search_params,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status != 200:
                        LOGGER.error(f"TMDb search ({endpoint}) failed for '{title}': HTTP {resp.status}")
                        continue
                    data = await resp.json(content_type=None)
                    results = data.get("results") or []
                    if results:
                        result = results[0]
                        break

            if not result:
                return None

            backdrop_path = result.get("backdrop_path") or result.get("poster_path")
            if not backdrop_path:
                return None

            image_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}"
            async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=20)) as img_resp:
                if img_resp.status == 200:
                    return await img_resp.read()
                LOGGER.error(f"TMDb backdrop download failed for '{title}': HTTP {img_resp.status}")
                return None
    except aiohttp.ClientError as e:
        LOGGER.error(f"TMDb network error for '{title}': {str(e)}")
    except asyncio.TimeoutError:
        LOGGER.error(f"TMDb request timed out for '{title}'")
    except Exception as e:
        LOGGER.error(f"TMDb unexpected error for '{title}': {str(e)}")
    return None


async def fetch_custom_poster(title: str, year: Optional[int] = None) -> Optional[bytes]:
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
