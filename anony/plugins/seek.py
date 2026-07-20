# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import anon, app, db, lang, queue
from anony.helpers import can_manage_vc


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


async def edit_rich(msg: types.Message, markdown: str):
    return await app.edit_message_text(
        chat_id=msg.chat.id,
        message_id=msg.id,
        rich_message=rich(markdown),
    )


@app.on_message(filters.command(["seek", "seekback"]) & filters.group & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _seek(_, m: types.Message):
    if len(m.command) < 2:
        return await reply_rich(m, m.lang["play_seek_usage"].format(m.command[0]))

    try:
        to_seek = int(m.command[1])
    except ValueError:
        return await reply_rich(m, m.lang["play_seek_usage"].format(m.command[0]))
    if to_seek < 10:
        return await reply_rich(m, m.lang["play_seek_min"])

    if not await db.get_call(m.chat.id):
        return await reply_rich(m, m.lang["not_playing"])

    if not await db.playing(m.chat.id):
        return await reply_rich(m, m.lang["play_already_paused"])

    media = queue.get_current(m.chat.id)
    if not media.duration_sec:
        return await reply_rich(m, m.lang["play_seek_no_dur"])

    sent = await reply_rich(m, m.lang["play_seeking"])
    if m.command[0] == "seekback":
        stype = m.lang["backward"]
        start_from = media.time - to_seek
        if start_from < 1:
            start_from = 1
    else:
        stype = m.lang["forward"]
        start_from = media.time + to_seek
        if start_from + 10 > media.duration_sec:
            start_from = media.duration_sec - 5

    await anon.play_media(m.chat.id, sent, media, start_from)
    media.time = start_from
    await edit_rich(
        sent, m.lang["play_seeked"].format(stype, start_from, m.from_user.first_name)
    )
