# helper_func.py

from data.access import get_approved_groups
from pyrogram.types import CallbackQuery

async def is_group_allowed(query: CallbackQuery) -> bool:
    if query.message.chat.type in ["group", "supergroup"]:
        allowed_groups = await get_approved_groups()
        return query.message.chat.id in allowed_groups
    return True  # PM हमेशा allow होता है
