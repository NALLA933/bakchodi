# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import time
import psutil

from pyrogram import filters, types

from anony import anon, app, boot, config, lang
from anony.helpers import buttons


def rich(markdown: str) -> types.InputRichMessage:
    return types.InputRichMessage(markdown=markdown)


@app.on_message(filters.command(["alive", "ping"]) & ~app.bl_users)
@lang.language()
async def _ping(_, m: types.Message):
    start = time.time()

    waiting = await app.send_rich_message(
        chat_id=m.chat.id,
        rich_message=rich(m.lang["pinging"]),
        reply_parameters=types.ReplyParameters(
            message_id=m.id
        ),
    )

    uptime = int(time.time() - boot)

    def get_time(seconds):
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")

        return " ".join(parts)

    latency = round((time.time() - start) * 1000, 2)

    await waiting.delete()

    await m.reply_photo(
        photo=config.PING_IMG,
        quote=True,
    )

    await app.send_rich_message(
        chat_id=m.chat.id,
        rich_message=rich(
            m.lang["ping_pong"].format(
                latency,
                get_time(uptime),
                psutil.cpu_percent(interval=0),
                psutil.virtual_memory().percent,
                psutil.disk_usage("/").percent,
                await anon.ping(),
            )
        ),
        reply_markup=buttons.ping_markup(
            m.lang["support"]
        ),
    )