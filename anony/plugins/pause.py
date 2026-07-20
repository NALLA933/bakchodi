# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import anon, app, db, lang
from anony.helpers import buttons, can_manage_vc


def rich(markdown: str) -> types.InputRichMessage:
    return types.InputRichMessage(markdown=markdown)


async def reply_rich(m: types.Message, markdown: str, reply_markup=None):
    return await app.send_rich_message(
        chat_id=m.chat.id,
        rich_message=rich(markdown),
        reply_markup=reply_markup,
        reply_parameters=types.ReplyParameters(
            message_id=m.id
        ),
    )


@app.on_message(filters.command(["pause"]) & filters.group & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _pause(_, m: types.Message):
    if not await db.get_call(m.chat.id):
        return await reply_rich(m, m.lang["not_playing"])

    if not await db.playing(m.chat.id):
        return await reply_rich(m, m.lang["play_already_paused"])

    await anon.pause(m.chat.id)
    await reply_rich(
        m,
        m.lang["play_paused"].format(m.from_user.first_name),
        reply_markup=buttons.controls(m.chat.id),
    )
