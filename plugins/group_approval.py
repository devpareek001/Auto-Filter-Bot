from pyrogram import Client, filters
from info import ENABLE_GROUP_APPROVAL, OWNER_ID, APPROVED_GROUPS

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
                "⚠️ Is group me bot use karne ke liye owner se permission lo."
            )
            await client.send_message(
                OWNER_ID,
                f"🔔 Bot ko add kiya gaya hai group: {chat_member_updated.chat.title} ({group_id})\nApprove karne ke liye: /approve {group_id}"
            )

@Client.on_message(filters.group)
async def block_unapproved_groups(client, message):
    if not ENABLE_GROUP_APPROVAL:
        return

    if message.chat.id not in APPROVED_GROUPS:
        return  # Bilkul silent

@Client.on_message(filters.private & filters.command("approve"))
async def approve_group(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("Aap owner nahi hain.")
        return
    try:
        group_id = int(message.text.split(maxsplit=1)[1])
        APPROVED_GROUPS.add(group_id)
        await message.reply("Group approved!")
        await client.send_message(group_id, "✅ Owner ne approval de diya hai, ab bot use kar sakte ho.")
    except:
        await message.reply("❌ Galat group ID.")
