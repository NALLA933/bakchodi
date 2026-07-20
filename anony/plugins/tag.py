import asyncio
import logging
import random
import time

from pyrogram import filters, enums
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait, UserNotParticipant, ChatAdminRequired
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from anony import app

logger = logging.getLogger("tagall")

PREFIXES        = ["!", "/", ".", "@", ":"]
TAG_COMMANDS    = ["utag", "all", "mention", "tag", "tagall", "mentionall"]
STOP_COMMANDS   = ["cancel", "ustop", "stoptag", "canceltag"]
FILTER_FLAGS    = {
    "--admins": enums.ChatMembersFilter.ADMINISTRATORS,
    "--recent": enums.ChatMembersFilter.RECENT,
    "--bots": enums.ChatMembersFilter.BOTS,
}
BATCH_SIZE      = 5
BATCH_DELAY     = 4.5
PROGRESS_EVERY  = 30
ADMIN_CACHE_TTL = 120

TAG_EMOJIS = [
    "👍🏻", "🔥", "✨", "🎯", "💫", "⚡", "🌟", "🎉", "💥", "🌈",
    "💎", "🦄", "🐝", "🌙", "🪐", "🌸", "🎀", "💖", "😎", "🥳",
]

active_tags: set[int] = set()
admin_cache: dict[tuple[int, int], tuple[bool, float]] = {}


def multi_prefix(commands: list[str]):
    triggers = [p + c for p in PREFIXES for c in commands]

    async def _check(_, __, message: Message) -> bool:
        return bool(message.text) and message.text.startswith(tuple(triggers))

    return filters.create(_check)


def extract_custom_text(text: str) -> str | None:
    for prefix in PREFIXES:
        for cmd in TAG_COMMANDS:
            if text.startswith(prefix + cmd):
                body = text[len(prefix) + len(cmd):].strip()
                for flag in FILTER_FLAGS:
                    body = body.replace(flag, "").strip()
                return body or None
    return None


def emoji_tag(user_id: int) -> str:
    return f'<a href="tg://user?id={user_id}">{random.choice(TAG_EMOJIS)}</a>'


def stop_button(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⛔ Stop Tagging", callback_data=f"stoptag_{chat_id}")]])


def parse_chat_id(data: str) -> int | None:
    try:
        return int(data.split("_", 1)[1])
    except (IndexError, ValueError):
        return None


async def safe_edit(message: Message, text: str, **kwargs) -> None:
    try:
        await message.edit_text(text, **kwargs)
    except Exception:
        pass


async def is_admin(chat_id: int, user_id: int) -> bool:
    if user_id in getattr(app, "sudoers", []):
        return True

    key = (chat_id, user_id)
    cached = admin_cache.get(key)
    if cached and time.monotonic() - cached[1] < ADMIN_CACHE_TTL:
        return cached[0]

    try:
        member = await app.get_chat_member(chat_id, user_id)
        result = member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)
    except UserNotParticipant:
        result = False
    except Exception as e:
        logger.error("Admin check failed uid=%s cid=%s: %s", user_id, chat_id, e)
        result = False

    admin_cache[key] = (result, time.monotonic())
    return result


async def is_authorized(m: Message) -> bool:
    if m.sender_chat and m.sender_chat.id == m.chat.id:
        return True
    if not m.from_user:
        return False
    return await is_admin(m.chat.id, m.from_user.id)


async def react_ack(message: Message) -> None:
    try:
        await app.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji="🍓")
    except Exception:
        pass


async def send_batch(
    chat_id: int,
    reply_to_id: int | None,
    custom_text: str | None,
    batch: list[int],
    start: int,
    end: int,
    *,
    retries: int = 5,
) -> None:
    parts = [custom_text] if custom_text else []
    parts.append("  ".join(emoji_tag(uid) for uid in batch))
    parts.append(f"<b>Tagged:</b> {start}–{end}")
    text = "\n\n".join(parts)

    kwargs: dict = {"disable_web_page_preview": True}
    if reply_to_id:
        kwargs["reply_to_message_id"] = reply_to_id

    for attempt in range(retries):
        try:
            return await app.send_message(chat_id, text, **kwargs)
        except FloodWait as e:
            logger.warning("FloodWait %ss batch %s-%s attempt %s", e.value + 2, start, end, attempt + 1)
            await asyncio.sleep(e.value + 2)
        except Exception as e:
            logger.error("Batch send failed attempt=%s cid=%s: %s", attempt + 1, chat_id, e)
            await asyncio.sleep(1)
    logger.error("Giving up on batch %s-%s in chat %s after %s retries", start, end, chat_id, retries)


@app.on_message(multi_prefix(TAG_COMMANDS) & filters.group & ~app.bl_users)
async def tag_all(_, m: Message):
    chat_id = m.chat.id

    if not await is_authorized(m):
        return await m.reply_text("🚫 <b>Admins only.</b>")

    if chat_id in active_tags:
        return await m.reply_text("⚠️ <b>Tagging already in progress.</b>", reply_markup=stop_button(chat_id))

    text = m.text or ""
    member_filter = next((v for k, v in FILTER_FLAGS.items() if k in text), None)
    filter_label = next((k.lstrip("-") for k in FILTER_FLAGS if k in text), "all members")

    custom_text = extract_custom_text(text)
    reply_to_id = m.reply_to_message.id if m.reply_to_message else None

    active_tags.add(chat_id)
    await react_ack(m)

    batch: list[int] = []
    total = sent = 0

    progress = await m.reply_text(
        f"⏳ <b>Starting tagging…</b> (<i>{filter_label}</i>)", reply_markup=stop_button(chat_id)
    )

    try:
        kwargs: dict = {"chat_id": chat_id}
        if member_filter is not None:
            kwargs["filter"] = member_filter
        members_iter = app.get_chat_members(**kwargs)

        async for member in members_iter:
            if chat_id not in active_tags:
                return await safe_edit(progress, "⛔ <b>Tagging stopped.</b>")

            user = member.user
            if not user or user.is_bot or user.is_deleted:
                continue

            batch.append(user.id)
            total += 1

            if len(batch) < BATCH_SIZE:
                continue

            sent += BATCH_SIZE
            await send_batch(chat_id, reply_to_id, custom_text, batch, sent - BATCH_SIZE + 1, sent)
            batch.clear()

            if sent % PROGRESS_EVERY == 0:
                await safe_edit(
                    progress,
                    f"⏳ <b>Tagging in progress…</b>\n<b>Tagged so far:</b> <code>{sent}</code>",
                    reply_markup=stop_button(chat_id),
                )

            await asyncio.sleep(BATCH_DELAY)

        if batch and chat_id in active_tags:
            sent += len(batch)
            await send_batch(chat_id, reply_to_id, custom_text, batch, sent - len(batch) + 1, sent)

        if chat_id in active_tags:
            await safe_edit(progress, f"✅ <b>Tagging complete!</b>\n<b>Total tagged:</b> <code>{total}</code>")

    except ChatAdminRequired:
        await safe_edit(progress, "❌ <b>Bot needs admin rights to fetch members.</b>")
    except FloodWait as e:
        logger.warning("FloodWait %ss fetching members in chat %s", e.value + 2, chat_id)
        await asyncio.sleep(e.value + 2)
        await safe_edit(progress, "⚠️ <b>Rate limited, please retry shortly.</b>")
    except Exception as e:
        logger.exception("Tagging failed in chat %s", chat_id)
        await safe_edit(progress, f"❌ <b>Error:</b> <code>{e}</code>")
    finally:
        active_tags.discard(chat_id)


@app.on_message(multi_prefix(STOP_COMMANDS) & filters.group & ~app.bl_users)
async def stop_tag(_, m: Message):
    chat_id = m.chat.id

    if chat_id not in active_tags:
        return await m.reply_text("ℹ️ <b>No tagging in progress.</b>")

    if not await is_authorized(m):
        return await m.reply_text("🚫 <b>Admins only.</b>")

    active_tags.discard(chat_id)
    await m.reply_text("✅ <b>Tagging stopped.</b>")


@app.on_callback_query(filters.regex(r"^stoptag_"))
async def cb_stop_tag(_, cq: CallbackQuery):
    chat_id = parse_chat_id(cq.data)
    if chat_id is None:
        return await cq.answer("Invalid data.", show_alert=True)

    if not await is_admin(chat_id, cq.from_user.id):
        return await cq.answer("Admins only.", show_alert=True)

    if chat_id not in active_tags:
        await cq.answer("No active tagging.", show_alert=True)
        try:
            await cq.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        return

    active_tags.discard(chat_id)
    await cq.answer("Stopped.", show_alert=False)
    await safe_edit(cq.message, "⛔ <b>Tagging stopped by</b> " + cq.from_user.mention)