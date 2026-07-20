# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from ntgcalls import (ConnectionNotFound, TelegramServerError,
                      RTMPStreamingUnsupported, ConnectionError)
from pyrogram.errors import MessageIdInvalid
from pyrogram.types import InputRichMessage, Message
from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls.pytgcalls_session import PyTgCallsSession

from anony import app, config, db, lang, logger, queue, userbot, yt
from anony.helpers import Media, Track, buttons


def rich(markdown: str) -> InputRichMessage:
    return InputRichMessage(markdown=markdown)


async def edit_rich(message: Message, markdown: str, reply_markup=None):
    return await app.edit_message_text(
        chat_id=message.chat.id,
        message_id=message.id,
        rich_message=rich(markdown),
        reply_markup=reply_markup,
    )


class TgCall(PyTgCalls):
    def __init__(self):
        self.clients = []

    async def pause(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=True)
        return await client.pause(chat_id)

    async def resume(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=False)
        return await client.resume(chat_id)

    async def stop(self, chat_id: int) -> None:
        client = await db.get_assistant(chat_id)
        queue.clear(chat_id)
        await db.remove_call(chat_id)

        try:
            await client.leave_call(chat_id, close=False)
        except Exception:
            pass


    async def play_media(
        self,
        chat_id: int,
        message: Message,
        media: Media | Track,
        seek_time: int = 0,
    ) -> None:
        client = await db.get_assistant(chat_id)
        _lang = await lang.get_lang(chat_id)

        if not media.file_path:
            await edit_rich(message, _lang["error_no_file"].format(config.SUPPORT_CHAT))
            return await self.play_next(chat_id)

        stream = types.MediaStream(
            media_path=media.file_path,
            audio_parameters=types.AudioQuality.HIGH,
            video_parameters=types.VideoQuality.HD_720p,
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=(
                types.MediaStream.Flags.AUTO_DETECT
                if media.video
                else types.MediaStream.Flags.IGNORE
            ),
            ffmpeg_parameters=f"-ss {seek_time}" if seek_time > 1 else None,
        )
        try:
            await client.play(
                chat_id=chat_id,
                stream=stream,
                config=types.GroupCallConfig(auto_start=False),
            )
            if not seek_time:
                media.time = 1
                await db.add_call(chat_id)
                text = _lang["play_media"].format(
                    media.url,
                    media.title,
                    media.duration,
                    media.user,
                )
                keyboard = buttons.controls(chat_id)
                try:
                    await edit_rich(message, text, reply_markup=keyboard)
                except MessageIdInvalid:
                    sent = await app.send_rich_message(
                        chat_id=chat_id,
                        rich_message=rich(text),
                        reply_markup=keyboard,
                    )
                    media.message_id = sent.message_id
        except FileNotFoundError:
            await edit_rich(message, _lang["error_no_file"].format(config.SUPPORT_CHAT))
            await self.play_next(chat_id)
        except exceptions.NoActiveGroupCall:
            await self.stop(chat_id)
            await edit_rich(message, _lang["error_no_call"])
        except exceptions.NoAudioSourceFound:
            await edit_rich(message, _lang["error_no_audio"])
            await self.play_next(chat_id)
        except (ConnectionError, ConnectionNotFound, TelegramServerError):
            await self.stop(chat_id)
            await edit_rich(message, _lang["error_tg_server"])
        except RTMPStreamingUnsupported:
            await self.stop(chat_id)
            await edit_rich(message, _lang["error_rtmp"])


    async def replay(self, chat_id: int) -> None:
        if not await db.get_call(chat_id):
            return

        media = queue.get_current(chat_id)
        _lang = await lang.get_lang(chat_id)
        msg = await app.send_rich_message(
            chat_id=chat_id,
            rich_message=rich(_lang["play_again"]),
        )
        await self.play_media(chat_id, msg, media)


    async def play_next(self, chat_id: int) -> None:
        loop_count = await db.get_loop(chat_id)
        if loop_count > 0:
            await db.set_loop(chat_id, loop_count - 1)
            return await self.replay(chat_id)

        media = queue.get_next(chat_id)

        if not media:
            return await self.stop(chat_id)

        try:
            if media.message_id:
                await app.delete_messages(
                    chat_id=chat_id,
                    message_ids=media.message_id,
                    revoke=True,
                )
                media.message_id = 0
        except Exception:
            pass

        _lang = await lang.get_lang(chat_id)
        msg = await app.send_rich_message(
            chat_id=chat_id,
            rich_message=rich(_lang["play_next"]),
        )
        if not media.file_path:
            media.file_path = await yt.download(media.id, video=media.video)
            if not media.file_path:
                await self.stop(chat_id)
                return await edit_rich(
                    msg, _lang["error_no_file"].format(config.SUPPORT_CHAT)
                )

        media.message_id = msg.message_id
        await self.play_media(chat_id, msg, media)


    async def ping(self) -> float:
        pings = [client.ping for client in self.clients]
        return round(sum(pings) / len(pings), 2)


    async def decorators(self, client: PyTgCalls) -> None:
        @client.on_update()
        async def update_handler(_, update: types.Update) -> None:
            if isinstance(update, types.StreamEnded):
                if update.stream_type == types.StreamEnded.Type.AUDIO:
                    await self.play_next(update.chat_id)
            elif isinstance(update, types.ChatUpdate):
                if update.status in [
                    types.ChatUpdate.Status.KICKED,
                    types.ChatUpdate.Status.LEFT_GROUP,
                    types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                ]:
                    await self.stop(update.chat_id)


    async def boot(self) -> None:
        PyTgCallsSession.notice_displayed = True
        for ub in userbot.clients:
            client = PyTgCalls(ub, cache_duration=100)
            await client.start()
            self.clients.append(client)
            await self.decorators(client)
        logger.info("PyTgCalls client(s) started.")
