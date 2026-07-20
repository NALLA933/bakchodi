# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import app, db, lang, queue
from anony.helpers import buttons


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


async def edit_rich(msg: types.Message, markdown: str, reply_markup=None):
    return await app.edit_message_text(
        chat_id=msg.chat.id,
        message_id=msg.id,
        rich_message=rich(markdown),
        reply_markup=reply_markup,
    )


@app.on_message(filters.command(["queue", "playing"]) & filters.group & ~app.bl_users)
@lang.language()
async def _queue_func(_, m: types.Message):
    if not await db.get_call(m.chat.id):
        return await reply_rich(m, m.lang["not_playing"])

    _reply = await reply_rich(m, m.lang["queue_fetching"])
    _queue = queue.get_queue(m.chat.id)
    _media = _queue[0]
    _text = m.lang["queue_curr"].format(
        _media.url,
        _media.title[:50],
        _media.duration,
        _media.user,
    )
    _queue.pop(0)

    if _queue:
        lines = []
        for i, media in enumerate(_queue, start=1):
            if i == 15:
                break
            lines.append(
                m.lang["queue_item"].format(i + 1, media.title, media.duration)
            )
        _text += "\n\n**>" + "\n>".join(lines) + "||"

    _playing = await db.playing(m.chat.id)
    _buttons = buttons.queue_markup(
            m.chat.id,
            m.lang["playing"] if _playing else m.lang["paused"],
            _playing,
        )
    await edit_rich(_reply, _text, reply_markup=_buttons)
