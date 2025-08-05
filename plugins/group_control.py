from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import ENABLE_GROUP_APPROVAL, OWNER_ID, CHANNEL_ID, OWNER_USERNAME
from data.access import get_approved_groups, approve_group_id  # ✅ import from data

# When bot is added to group
@Client.on_chat_member_updated()
async def group_add_check(client, chat_member_updated):
    if not ENABLE_GROUP_APPROVAL:
        return

    me = await client.get_me()
    if chat_member_updated.new_chat_member.user.id == me.id:
        group_id = chat_member_updated.chat.id
        approved = get_approved_groups()
        if group_id not in approved:
            await client.send_message(
                group_id,
                "⚠️ इस ग्रुप में बॉट का इस्तेमाल करने के लिए ओनर से परमिशन लो।",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("👤 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}")]]
                )
            )
            await client.send_message(
                CHANNEL_ID,
                f"📢 Bot को add किया गया है group: {chat_member_updated.chat.title} (`{group_id}`)\nApprove करने के लिए: `/approve {group_id}`"
            )

# Block bot in unapproved groups
@Client.on_message(filters.group)
async def block_unapproved_groups(client, message):
    if not ENABLE_GROUP_APPROVAL:
        return
    approved = get_approved_groups()
    if message.chat.id not in approved:
        return  # silence

# /approve command (only owner)
@Client.on_message(filters.private & filters.command("approve"))
async def approve_group(client, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ आप इस कमांड को इस्तेमाल नहीं कर सकते।")

    try:
        group_id = int(message.text.split(maxsplit=1)[1])
        approve_group_id(group_id)
        await message.reply(f"✅ Group `{group_id}` approved!")
        await client.send_message(group_id, "✅ इस ग्रुप को अब Bot इस्तेमाल कर सकता है।")
    except Exception as e:
        await message.reply(f"❌ Group ID गलत है।\n\nError: `{e}`")
