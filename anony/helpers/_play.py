import asyncio

from pyrogram import enums, errors, types

from anony import app, config, db, logger, queue, yt
from anony.helpers import utils

JOIN_RETRY_DELAY = 2
MAX_UNBAN_RETRIES = 2


def rich(markdown: str) -> types.InputRichMessage:
    return types.InputRichMessage(markdown=markdown)


async def reply_rich(m: types.Message, markdown: str):
    return await app.send_rich_message(
        chat_id=m.chat.id,
        rich_message=rich(markdown),
        reply_parameters=types.ReplyParameters(
            message_id=m.id
        ),
    )


async def unban_client(chat_id: int, client_id: int) -> bool:
    for attempt in range(MAX_UNBAN_RETRIES):
        try:
            await app.unban_chat_member(chat_id=chat_id, user_id=client_id)
            return True
        except errors.FloodWait as e:
            if e.value > 30:
                return False
            await asyncio.sleep(e.value)
        except errors.ChatAdminRequired:
            return False
        except Exception as ex:
            logger.error(f"Unban failed for {client_id} in {chat_id} (attempt {attempt + 1}): {ex}")
            return False
    return False


async def get_invite_link(chat_id: int):
    try:
        chat = await app.get_chat(chat_id)
        return chat.invite_link or await app.export_chat_invite_link(chat_id)
    except errors.ChatAdminRequired:
        return None
    except errors.FloodWait as e:
        await asyncio.sleep(min(e.value, 30))
        return await get_invite_link(chat_id)


async def join_client(m: types.Message, chat_id: int, client) -> bool:
    if m.chat.username:
        try:
            await client.resolve_peer(m.chat.username)
            return True
        except Exception:
            pass

    invite_link = await get_invite_link(chat_id)
    if not invite_link:
        await reply_rich(m, m.lang["admin_required"])
        return False

    umm = await reply_rich(m, m.lang["play_invite"].format(app.name))
    await asyncio.sleep(JOIN_RETRY_DELAY)
    try:
        await client.join_chat(invite_link)
    except errors.UserAlreadyParticipant:
        pass
    except errors.InviteRequestSent:
        await asyncio.sleep(JOIN_RETRY_DELAY)
        try:
            await app.approve_chat_join_request(chat_id, client.id)
        except errors.HideRequesterMissing:
            pass
        except Exception as ex:
            await app.edit_message_text(
                chat_id=m.chat.id,
                message_id=umm.id,
                rich_message=rich(
                    m.lang["play_invite_error"].format(type(ex).__name__)
                ),
            )
            return False
    except errors.FloodWait as e:
        await app.edit_message_text(
            chat_id=m.chat.id,
            message_id=umm.id,
            rich_message=rich(
                m.lang["play_invite_error"].format("FloodWait")
            ),
        )
        await asyncio.sleep(min(e.value, 30))
        return False
    except Exception as ex:
        logger.error(f"Error joining chat - {chat_id}: {ex}")
        await app.edit_message_text(
            chat_id=m.chat.id,
            message_id=umm.id,
            rich_message=rich(
                m.lang["play_invite_error"].format(type(ex).__name__)
            ),
        )
        return False

    await umm.delete()
    await client.resolve_peer(chat_id)
    return True


async def ensure_client_active(m: types.Message, chat_id: int) -> bool:
    if chat_id in db.active_calls:
        return True

    client = await db.get_client(chat_id)
    try:
        member = await app.get_chat_member(chat_id, client.id)
    except errors.ChatAdminRequired:
        await reply_rich(m, m.lang["admin_required"])
        return False
    except (errors.UserNotParticipant, errors.exceptions.bad_request_400.UserNotParticipant):
        return await join_client(m, chat_id, client)
    except errors.FloodWait as e:
        await asyncio.sleep(min(e.value, 30))
        return await ensure_client_active(m, chat_id)

    if member.status not in (enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.RESTRICTED):
        return True

    if not await unban_client(chat_id, client.id):
        await reply_rich(
            m,
            m.lang["play_banned"].format(
                app.name,
                client.id,
                client.first_name,
                f"@{client.username}" if client.username else None,
            ),
        )
        return False

    try:
        recheck = await app.get_chat_member(chat_id, client.id)
        if recheck.status == enums.ChatMemberStatus.MEMBER:
            return True
    except (errors.UserNotParticipant, errors.exceptions.bad_request_400.UserNotParticipant):
        pass
    except Exception as ex:
        logger.error(f"Recheck failed for {client.id} in {chat_id}: {ex}")

    return await join_client(m, chat_id, client)


def checkUB(play):
    async def wrapper(_, m: types.Message):
        if not m.from_user:
            return await reply_rich(m, m.lang["play_user_invalid"])

        chat_id = m.chat.id
        if m.chat.type != enums.ChatType.SUPERGROUP:
            await reply_rich(m, m.lang["play_chat_invalid"])
            return await app.leave_chat(chat_id)

        if not m.reply_to_message and (
            len(m.command) < 2 or (len(m.command) == 2 and m.command[1] == "-f")
        ):
            return await reply_rich(m, m.lang["play_usage"])

        if len(queue.get_queue(chat_id)) >= config.QUEUE_LIMIT:
            return await reply_rich(
                m, m.lang["play_queue_full"].format(config.QUEUE_LIMIT)
            )

        force = m.command[0].endswith("force") or (
            len(m.command) > 1 and "-f" in m.command[1]
        )
        video = m.command[0][0] == "v" and config.VIDEO_PLAY
        url = utils.get_url(m)
        if url and yt.invalid(url):
            return await reply_rich(
                m, m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )
        m3u8 = url and not yt.valid(url)

        play_mode = await db.get_play_mode(chat_id)
        if play_mode or force:
            adminlist = await db.get_admins(chat_id)
            if (
                m.from_user.id not in adminlist
                and not await db.is_auth(chat_id, m.from_user.id)
                and m.from_user.id not in app.sudoers
            ):
                return await reply_rich(m, m.lang["play_admin"])

        if not await ensure_client_active(m, chat_id):
            return

        if await db.get_cmd_delete(chat_id):
            try:
                await m.delete()
            except Exception:
                pass

        return await play(_, m, force, m3u8, video, url)

    return wrapper


def checkUBChannel(play):
    async def wrapper(_, m: types.Message):
        chat_id = m.chat.id
        if m.chat.type != enums.ChatType.CHANNEL:
            await reply_rich(m, m.lang["play_chat_invalid"])
            return await app.leave_chat(chat_id)

        if len(m.command) < 2:
            return await reply_rich(m, m.lang["play_usage"])

        if len(queue.get_queue(chat_id)) >= config.QUEUE_LIMIT:
            return await reply_rich(
                m, m.lang["play_queue_full"].format(config.QUEUE_LIMIT)
            )

        force = m.command[0].endswith("force")
        video = m.command[0][0] == "v" and config.VIDEO_PLAY
        url = utils.get_url(m)
        if url and yt.invalid(url):
            return await reply_rich(
                m, m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )
        m3u8 = url and not yt.valid(url)

        if not await ensure_client_active(m, chat_id):
            return

        return await play(_, m, force, m3u8, video, url)

    return wrapper
