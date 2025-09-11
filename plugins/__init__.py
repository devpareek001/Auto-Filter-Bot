from aiohttp import web
from .route import routes
from asyncio import sleep 
from datetime import datetime, timedelta
from database.extra_db import silicondb
from database.users_chats_db import db
from info import PREMIUM_LOGS, URL
from datetime import time
import pytz
import aiohttp
import asyncio
from logging_helper import LOGGER

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

REMINDER_TIMES = [
    ("10m", timedelta(minutes=10))
]

async def reset_file_limits_daily():
    tz = pytz.timezone('Asia/Kolkata')
    while True:
        now = datetime.now(tz)
        target_time = time(23, 59)
        target_datetime = tz.localize(datetime.combine(now.date(), target_time))
        if now > target_datetime:
            target_datetime += timedelta(days=1)
        time_diff = (target_datetime - now).total_seconds()
        await asyncio.sleep(time_diff)
        silicondb.reset_all_file_limits()
        logging.info("Files count reset successfully")

# Premium Reminder Expired ( This Code Modified By @BOT_OWNER26)
async def check_expired_premium(client):
    while True:
        now = datetime.utcnow()
        expired_users = await db.get_expired(now)
        for user in expired_users:
            user_id = user["id"]
            await db.remove_premium_access(user_id)
            unset_flags = {f"reminder_{label}_sent": "" for label, _ in REMINDER_TIMES}
            await db.users.update_one({"id": user_id}, {"$unset": unset_flags})
            try:
                tg_user = await client.get_users(user_id)
                await client.send_message(
                    user_id,
                    f"<b>ʜᴇʏ {tg_user.mention},\n\nʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss ʜᴀs ᴇxᴘɪʀᴇᴅ.\n\nTᴀᴘ /plan ꜰᴏʀ ʀᴇɴᴇᴡᴀʟ ᴏᴘᴛɪᴏɴs.</b>"
                )
                await client.send_message(
                    PREMIUM_LOGS,
                    f"<b>#Premium_Expired\nUser: {tg_user.mention}\nID: <code>{user_id}</code></b>"
                )
            except Exception as e:
                LOGGER.error(f"[EXPIRED ERROR] {e}")
            await sleep(0.5)
        for label, delta in REMINDER_TIMES:
            reminder_users = await db.get_expiring_soon(label, delta)
            for user in reminder_users:
                user_id = user["id"]
                try:
                    tg_user = await client.get_users(user_id)
                    await client.send_message(
                        user_id,
                        f"<b>ʜᴇʏ {tg_user.mention},\n\nʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ᴇxᴘɪʀᴇ ɪɴ {label}.\nTᴀᴘ /plan ᴛᴏ ʀᴇɴᴇᴡ ɴᴏᴡ!</b>"
                    )
                    await client.send_message(
                        PREMIUM_LOGS,
                        f"<b>#Reminder ({label})\nUser: {tg_user.mention}\nID: <code>{user_id}</code></b>"
                    )
                except Exception as e:
                    LOGGER.error(f"[REMINDER ERROR] {e}")
                await sleep(0.5)
        await sleep(1)

