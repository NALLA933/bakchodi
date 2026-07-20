from asyncio import gather, sleep
from datetime import datetime, timedelta, timezone
from itertools import islice
from pyrogram import filters
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.errors import MessageDeleteForbidden, RPCError, FloodWait, UserNotParticipant
from pyrogram.types import Message
from anony import app
OWNER_ID = [5147822244]
GROUPS = (ChatType.SUPERGROUP, ChatType.GROUP)
PURGE_LIMIT = timedelta(days=2)
MAX_PURGE_SPAN = 5000
MAX_FLOOD_RETRIES = 3
MAX_FLOOD_WAIT = 60
def batched(ids: range, size: int = 100):
    it = iter(ids)
    while batch := list(islice(it, size)):
        yield batch
def within_purge_limit(date: datetime) -> bool:
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - date <= PURGE_LIMIT
async def can_delete_messages(chat_id: int, user_id: int) -> bool:
    if user_id in OWNER_ID:
        return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        if member.status == ChatMemberStatus.OWNER:
            return True
        return bool(member.status == ChatMemberStatus.ADMINISTRATOR and member.privileges and member.privileges.can_delete_messages)
    except (UserNotParticipant, RPCError):
        return False
async def purge_range(chat_id: int, start_id: int, end_id: int) -> int:
    deleted = 0
    for chunk in batched(range(start_id, end_id + 1)):
        retries = 0
        while retries < MAX_FLOOD_RETRIES:
            try:
                await app.delete_messages(chat_id, chunk, revoke=True)
                deleted += len(chunk)
                break
            except FloodWait as e:
                if e.value > MAX_FLOOD_WAIT:
                    raise
                await sleep(e.value)
                retries += 1
            except RPCError:
                break
    return deleted
async def flash(m: Message, text: str, delay: int = 2):
    status = await m.reply_text(text)
    await sleep(delay)
    await status.delete()
@app.on_message(filters.command(["purge", "spurge"]) & filters.group & ~app.bl_users)
async def purge_messages(_, m: Message):
    silent = m.command[0] == "spurge"
    if m.chat.type not in GROUPS or not m.reply_to_message or not await can_delete_messages(m.chat.id, m.from_user.id):
        return None if silent else await m.reply_text("<b>Reply to a message with permission to purge</b>")
    if not within_purge_limit(m.reply_to_message.date):
        return None if silent else await m.reply_text("<b>Cannot purge messages older than 2 days</b>")
    if m.id - m.reply_to_message.id > MAX_PURGE_SPAN:
        return None if silent else await m.reply_text(f"<b>Cannot purge more than {MAX_PURGE_SPAN} messages at once</b>")
    try:
        deleted = await purge_range(m.chat.id, m.reply_to_message.id, m.id)
        if not silent:
            await flash(m, f"<b>Deleted {deleted} messages</b>")
    except MessageDeleteForbidden:
        if not silent:
            await m.reply_text("<b>Missing permissions to delete messages</b>")
    except FloodWait as e:
        if not silent:
            await m.reply_text(f"<b>Flood wait hit, try again in {e.value}s</b>")
    except RPCError:
        if not silent:
            await m.reply_text("<b>Purge failed due to a Telegram error</b>")
@app.on_message(filters.command("del") & filters.group & ~app.bl_users)
async def delete_message(_, m: Message):
    if m.chat.type not in GROUPS or not m.reply_to_message or not await can_delete_messages(m.chat.id, m.from_user.id):
        return await m.reply_text("<b>Reply to a message with permission to delete</b>")
    try:
        await app.delete_messages(m.chat.id, [m.reply_to_message.id, m.id])
    except MessageDeleteForbidden:
        await m.reply_text("<b>Missing permissions to delete messages</b>")
