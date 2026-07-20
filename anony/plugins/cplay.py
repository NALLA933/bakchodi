from pathlib import Path

from pyrogram import filters, types

from anony import anon, app, config, db, lang, queue, tg, yt
from anony.helpers import buttons, utils
from anony.helpers._play import checkUBChannel


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


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    lines = []
    total = 0
    for track in tracks:
        pos = queue.add(chat_id, track)
        line = f"**{pos}.** {track.title}"
        if total + len(line) > 1948:
            break
        lines.append(line)
        total += len(line)
    return "**>" + "\n>".join(lines) + "||"


@app.on_message(
    filters.command(["cplay", "cplayforce"])
    & filters.channel
    & ~app.bl_users
)
@lang.language()
@checkUBChannel
async def cplay_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    m3u8: bool = False,
    video: bool = False,
    url: str = None,
) -> None:
    sent = await reply_rich(m, m.lang["play_searching"])
    mention = m.sender_chat.title if m.sender_chat else app.name
    tracks = []
    file = None

    try:
        if m3u8:
            file = await tg.process_m3u8(url, sent.id, video)

        elif url:
            if "playlist" in url:
                await edit_rich(sent, m.lang["playlist_fetch"])
                tracks = await yt.playlist(config.PLAYLIST_LIMIT, mention, url, video)
                if not tracks:
                    return await edit_rich(sent, m.lang["playlist_error"])
                file = tracks.pop(0)
                file.message_id = sent.id
            else:
                file = await yt.search(url, sent.id, video=video)

            if not file:
                return await edit_rich(
                    sent, m.lang["play_not_found"].format(config.SUPPORT_CHAT)
                )

        elif len(m.command) >= 2:
            query = " ".join(m.command[1:])
            file = await yt.search(query, sent.id, video=video)
            if not file:
                return await edit_rich(
                    sent, m.lang["play_not_found"].format(config.SUPPORT_CHAT)
                )
    except Exception:
        return await edit_rich(
            sent, m.lang["play_not_found"].format(config.SUPPORT_CHAT)
        )

    if not file:
        return await edit_rich(sent, m.lang["play_usage"])

    if config.DURATION_LIMIT and file.duration_sec > config.DURATION_LIMIT:
        return await edit_rich(
            sent, m.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60)
        )

    if await db.is_logger():
        await utils.play_log(m, sent.link, file.title, file.duration)

    file.user = mention

    if force:
        queue.force_add(m.chat.id, file)
    else:
        position = queue.add(m.chat.id, file)
        if position != 0 or await db.get_call(m.chat.id):
            await edit_rich(
                sent,
                m.lang["play_queued"].format(
                    position, file.url, file.title, file.duration, mention
                ),
                reply_markup=buttons.play_queued(m.chat.id, file.id, m.lang["play_now"]),
            )
            if tracks:
                await app.send_rich_message(
                    chat_id=m.chat.id,
                    rich_message=rich(
                        m.lang["playlist_queued"].format(len(tracks))
                        + playlist_to_queue(m.chat.id, tracks)
                    ),
                )
            return

    if not file.file_path:
        fname = f"downloads/{file.id}.{'mp4' if video else 'webm'}"
        if Path(fname).exists():
            file.file_path = fname
        else:
            await edit_rich(sent, m.lang["play_downloading"])
            try:
                file.file_path = await yt.download(file.id, video=video)
            except Exception:
                return await edit_rich(
                    sent, m.lang["play_not_found"].format(config.SUPPORT_CHAT)
                )

    try:
        await anon.play_media(chat_id=m.chat.id, message=sent, media=file)
    except Exception:
        return await edit_rich(
            sent, m.lang["play_not_found"].format(config.SUPPORT_CHAT)
        )

    if tracks:
        await app.send_rich_message(
            chat_id=m.chat.id,
            rich_message=rich(
                m.lang["playlist_queued"].format(len(tracks))
                + playlist_to_queue(m.chat.id, tracks)
            ),
        )


@app.on_message(
    filters.command(["cend", "cstop"])
    & filters.channel
    & ~app.bl_users
)
@lang.language()
async def cend_hndlr(_, m: types.Message) -> None:
    if not await db.get_call(m.chat.id):
        return await reply_rich(m, m.lang["end_no_call"])

    await anon.stop(m.chat.id)
    await reply_rich(m, m.lang["end_success"])
