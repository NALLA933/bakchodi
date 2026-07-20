# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import anon, app, db, lang
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


@app.on_message(filters.command(["end", "stop"]) & filters.group & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _stop(_, m: types.Message):
    if len(m.command) > 1:
        return

    call = await db.get_call(m.chat.id)
    await anon.stop(m.chat.id)
    if not call:
        return await reply_rich(m, m.lang["not_playing"])

    await reply_rich(m, m.lang["play_stopped"].format(m.from_user.first_name))
