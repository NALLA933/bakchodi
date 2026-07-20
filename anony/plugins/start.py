# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import asyncio
from pyrogram import enums, filters, types
from pyrogram.types import ReplyParameters

from anony import app, config, db, lang
from anony.helpers import buttons, utils


def rich(markdown: str) -> types.InputRichMessage:
    return types.InputRichMessage(markdown=markdown)


@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
@lang.language()
async def _help(_, m: types.Message):
    await app.send_rich_message(
        chat_id=m.chat.id,
        rich_message=rich(m.lang["help_menu"]),
        reply_parameters=ReplyParameters(
            message_id=m.id
        ),
        reply_markup=buttons.help_markup(m.lang),
    )


@app.on_message(filters.command(["start"]))
@lang.language()
async def start(_, message: types.Message):
    if (
        message.from_user.id in app.bl_users
        and message.from_user.id not in db.notified
    ):
        return await app.send_rich_message(
            chat_id=message.chat.id,
            rich_message=rich(message.lang["bl_user_notify"]),
            reply_parameters=ReplyParameters(message_id=message.id),
        )

    if len(message.command) > 1 and message.command[1] == "help":
        return await _help(_, message)

    private = message.chat.type == enums.ChatType.PRIVATE

    text = (
        message.lang["start_pm"].format(
            message.from_user.first_name,
            app.name,
        )
        if private
        else message.lang["start_gp"].format(app.name)
    )

    key = buttons.start_key(message.lang, private)

    # Send the photo
    await message.reply_photo(
        photo=config.START_IMG,
        quote=not private,
    )

    # Send the Rich Message
    await app.send_rich_message(
        chat_id=message.chat.id,
        rich_message=rich(text),
        reply_markup=key,
    )

    if private:
        if not await db.is_user(message.from_user.id):
            await utils.send_log(message)
            await db.add_user(message.from_user.id)
    else:
        if not await db.is_chat(message.chat.id):
            await utils.send_log(message, True)
            await db.add_chat(message.chat.id)


@app.on_message(
    filters.command(["playmode", "settings"])
    & filters.group
    & ~app.bl_users
)
@lang.language()
async def settings(_, message: types.Message):
    admin_only = await db.get_play_mode(message.chat.id)
    cmd_delete = await db.get_cmd_delete(message.chat.id)
    _language = await db.get_lang(message.chat.id)

    await app.send_rich_message(
        chat_id=message.chat.id,
        rich_message=rich(
            message.lang["start_settings"].format(
                message.chat.title
            )
        ),
        reply_parameters=ReplyParameters(
            message_id=message.id
        ),
        reply_markup=buttons.settings_markup(
            message.lang,
            admin_only,
            cmd_delete,
            _language,
            message.chat.id,
        ),
    )


@app.on_message(filters.new_chat_members, group=7)
@lang.language()
async def _new_member(_, message: types.Message):
    if message.chat.type != enums.ChatType.SUPERGROUP:
        return await message.chat.leave()

    await asyncio.sleep(3)

    for member in message.new_chat_members:
        if member.id == app.id:
            if await db.is_chat(message.chat.id):
                return

            await utils.send_log(message, True)
            await db.add_chat(message.chat.id)
