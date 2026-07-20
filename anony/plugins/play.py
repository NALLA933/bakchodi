from pathlib import Path

from pyrogram import filters, types

from anony import anon, app, config, db, lang, queue, tg, yt
from anony.helpers import buttons, utils
from anony.helpers._play import checkUB


def rich(markdown: str) -> types.InputRichMessage:
    return types.InputRichMessage(markdown=markdown)


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    lines = []

    for track in tracks:
        pos = queue.add(chat_id, track)
        lines.append(f"{pos}. **{track.title}**")

    return (
        "<details>\n"
        "<summary>Queued Tracks</summary>\n\n"
        + "\n".join(lines)
        + "\n</details>"
    )


@app.on_message(
    filters.command(["play", "playforce", "vplay", "vplayforce"])
    & filters.group
    & ~app.bl_users
)
@lang.language()
@checkUB
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    m3u8: bool = False,
    video: bool = False,
    url: str = None,
):
    sent = await app.send_rich_message(
        chat_id=m.chat.id,
        rich_message=rich(m.lang["play_searching"]),
        reply_parameters=types.ReplyParameters(
            message_id=m.id
        ),
    )

    mention = (
        m.from_user.first_name
        if m.from_user
        else (
            m.sender_chat.title
            if m.sender_chat
            else "Anonymous"
        )
    )

    media = (
        tg.get_media(m.reply_to_message)
        if m.reply_to_message
        else None
    )

    tracks = []
    file = None

    try:
        if media:
            setattr(sent, "lang", m.lang)
            file = await tg.download(
                m.reply_to_message,
                sent,
            )

        elif m3u8:
            file = await tg.process_m3u8(
                url,
                sent.id,
                video,
            )

        elif url:

            if "playlist" in url:

                await app.edit_message_text(
                    chat_id=m.chat.id,
                    message_id=sent.id,
                    rich_message=rich(
                        m.lang["playlist_fetch"]
                    ),
                )

                tracks = await yt.playlist(
                    config.PLAYLIST_LIMIT,
                    mention,
                    url,
                    video,
                )

                if not tracks:
                    return await app.edit_message_text(
                        chat_id=m.chat.id,
                        message_id=sent.id,
                        rich_message=rich(
                            m.lang["playlist_error"]
                        ),
                    )

                file = tracks.pop(0)
                file.message_id = sent.id

            else:
                file = await yt.search(
                    url,
                    sent.id,
                    video=video,
                )

            if not file:
                return await app.edit_message_text(
                    chat_id=m.chat.id,
                    message_id=sent.id,
                    rich_message=rich(
                        m.lang["play_not_found"].format(
                            config.SUPPORT_CHAT
                        )
                    ),
                )

        elif len(m.command) >= 2:

            query = " ".join(m.command[1:])

            file = await yt.search(
                query,
                sent.id,
                video=video,
            )

            if not file:
                return await app.edit_message_text(
                    chat_id=m.chat.id,
                    message_id=sent.id,
                    rich_message=rich(
                        m.lang["play_not_found"].format(
                            config.SUPPORT_CHAT
                        )
                    ),
                )

    except Exception:

        return await app.edit_message_text(
            chat_id=m.chat.id,
            message_id=sent.id,
            rich_message=rich(
                m.lang["play_not_found"].format(
                    config.SUPPORT_CHAT
                )
            ),
        )

    if not file:
        return await app.edit_message_text(
            chat_id=m.chat.id,
            message_id=sent.id,
            rich_message=rich(
                m.lang["play_usage"]
            ),
        )

    if (
        config.DURATION_LIMIT
        and file.duration_sec > config.DURATION_LIMIT
    ):
        return await app.edit_message_text(
            chat_id=m.chat.id,
            message_id=sent.id,
            rich_message=rich(
                m.lang["play_duration_limit"].format(
                    config.DURATION_LIMIT // 60
                )
            ),
        )

    if await db.is_logger():
        await utils.play_log(
            m,
            sent.link,
            file.title,
            file.duration,
        )

    file.user = mention

    if force:
        queue.force_add(
            m.chat.id,
            file,
        )

    else:
        position = queue.add(
            m.chat.id,
            file,
        )

        if (
            position != 0
            or await db.get_call(m.chat.id)
        ):

            await app.edit_message_text(
                chat_id=m.chat.id,
                message_id=sent.id,
                rich_message=rich(
                    m.lang["play_queued"].format(
                        position,
                        file.url,
                        file.title,
                        file.duration,
                        mention,
                    )
                ),
                reply_markup=buttons.play_queued(
                    m.chat.id,
                    file.id,
                    m.lang["play_now"],
                ),
            )

            if tracks:
                await app.send_rich_message(
                    chat_id=m.chat.id,
                    rich_message=rich(
                        m.lang["playlist_queued"].format(
                            len(tracks)
                        )
                        + "\n\n"
                        + playlist_to_queue(
                            m.chat.id,
                            tracks,
                        )
                    ),
                )

            return

    if not file.file_path:

        fname = (
            f"downloads/{file.id}."
            f"{'mp4' if video else 'webm'}"
        )

        if Path(fname).exists():

            file.file_path = fname

        else:

            await app.edit_message_text(
                chat_id=m.chat.id,
                message_id=sent.id,
                rich_message=rich(
                    m.lang["play_downloading"]
                ),
            )

            try:
                file.file_path = await yt.download(
                    file.id,
                    video=video,
                )

            except Exception:
                return await app.edit_message_text(
                    chat_id=m.chat.id,
                    message_id=sent.id,
                    rich_message=rich(
                        m.lang["play_not_found"].format(
                            config.SUPPORT_CHAT
                        )
                    ),
                )

    try:

        await anon.play_media(
            chat_id=m.chat.id,
            message=sent,
            media=file,
        )

    except Exception:

        return await app.edit_message_text(
            chat_id=m.chat.id,
            message_id=sent.id,
            rich_message=rich(
                m.lang["play_not_found"].format(
                    config.SUPPORT_CHAT
                )
            ),
        )

    if tracks:

        await app.send_rich_message(
            chat_id=m.chat.id,
            rich_message=rich(
                m.lang["playlist_queued"].format(
                    len(tracks)
                )
                + "\n\n"
                + playlist_to_queue(
                    m.chat.id,
                    tracks,
                )
            ),
        )
