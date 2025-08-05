from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import ENABLE_GROUP_APPROVAL, OWNER_ID, CHANNEL_ID, OWNER_USERNAME
from access import get_approved_groups, approve_group_id

APPROVED_GROUPS = get_approved_groups()

@Client.on_chat_member_updated()
async def group_add_check(client, chat_member_updated):
    if not ENABLE_GROUP_APPROVAL:
        return

    me = await client.get_me()
    if chat_member_updated.new_chat_member.user.id == me.id:
        group_id = chat_member_updated.chat.id
        if group_id not in APPROVED_GROUPS:
            await client.send_message(
                group_id,
                "⚠️ Is group me bot use karne ke liye owner se permission lo.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("👤 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}")]]
                )
            )
            await client.send_message(
                CHANNEL_ID,
                f"🔔 Bot ko add kiya gaya hai group: {chat_member_updated.chat.title} ({group_id})\nApprove karne ke liye: /approve {group_id}"
            )

@Client.on_message(filters.group)
async def block_unapproved_groups(client, message):
    if not ENABLE_GROUP_APPROVAL:
        return
    if message.chat.id not in get_approved_groups():
        return  # Silence the bot

@Client.on_message(filters.private & filters.command("approve"))
async def approve_group(client, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("Aap owner nahi hain.")
    try:
        group_id = int(message.text.split(maxsplit=1)[1])
        approve_group_id(group_id)
        await message.reply("✅ Group approved!")
        await client.send_message(group_id, "✅ Owner ne approval de diya hai, ab bot use kar sakte ho.")
    except Exception as e:
        await message.reply(f"❌ Galat group ID. Error: {e}")
