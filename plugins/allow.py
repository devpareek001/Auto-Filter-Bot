from pyrogram import Client, filters
from pyrogram.types import Message
from helpers.allowlist import save_allowed_group
from info import OWNER_ID  # assuming OWNER_ID is in info.py

Bot = Client("SilentXBotz")  # <- Add your bot session name if needed

@Bot.on_message(filters.command("allow") & filters.private)
async def allow_group(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("Only owner can use this command.")

    if len(message.command) < 2:
        return await message.reply("Usage: /allow group_id")

    try:
        group_id = int(message.command[1])
    except ValueError:
        return await message.reply("Invalid group ID.")

    save_allowed_group(group_id)
    await message.reply(f"✅ Group `{group_id}` is now allowed.")
