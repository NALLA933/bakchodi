import os
import glob
import shutil
from asyncio import gather
from functools import lru_cache
from traceback import format_exc

from PIL import Image, ImageDraw, ImageFont
from pyrogram import filters, raw, enums
from pyrogram.errors import (
    PeerIdInvalid,
    ShortnameOccupyFailed,
    StickerEmojiInvalid,
    StickerPngDimensions,
    StickerPngNopng,
    UserIsBlocked,
)
from pyrogram.file_id import FileId
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from anony import app
from .er import capture_err
from .files import get_document_from_file_id, upload_document
from .st import (
    add_sticker_to_set,
    create_sticker,
    create_sticker_set,
    detect_sticker_type,
    get_sticker_set_by_name,
    remove_sticker_from_set,
)

MAX_STICKERS = 120
STATIC_TYPES = {"jpeg", "jpg", "png", "webp", "bmp", "gif", "tiff", "tif", "ico"}
ALL_TYPES = STATIC_TYPES | {"tgs", "webm"}
TMP = "/tmp"
SYSTEM_FONTS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
)


def _cleanup(*paths):
    for p in filter(None, paths):
        if os.path.isfile(p):
            os.remove(p)


def _fit_512(img: Image.Image) -> Image.Image:
    w, h = img.size
    if max(w, h) == 512:
        return img
    scale = 512 / max(w, h)
    return img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)


def _to_png(src: str) -> str:
    dst = src.rsplit(".", 1)[0] + ".png"
    with Image.open(src) as img:
        _fit_512(img.convert("RGBA")).save(dst, "PNG", optimize=True)
    return dst


@lru_cache(maxsize=1)
def _font_path() -> str:
    for f in (*SYSTEM_FONTS, *glob.glob("/usr/share/fonts/**/*.ttf", recursive=True)):
        if os.path.isfile(f):
            path = f"{TMP}/mmf_font.ttf"
            shutil.copy(f, path)
            return path
    raise RuntimeError("no font available on this system")


@lru_cache(maxsize=64)
def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(_font_path(), size)


def _stamp(draw: ImageDraw.ImageDraw, text: str, w: int, h: int, top: bool):
    size = 80
    while size > 10:
        x0, _, x1, _ = _font(size).getbbox(text)
        if x1 - x0 <= w - 24:
            break
        size -= 2
    fnt = _font(size)
    x0, y0, x1, y1 = fnt.getbbox(text)
    x, y = (w - (x1 - x0)) // 2, (12 if top else h - (y1 - y0) - 24)
    for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        draw.text((x + ox, y + oy), text, font=fnt, fill=(0, 0, 0, 255))
    draw.text((x, y), text, font=fnt, fill=(255, 255, 255, 255))


def _render(path: str, top: str, bottom: str) -> Image.Image:
    with Image.open(path) as base:
        img = base.convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")
    w, h = img.size
    for text, is_top in ((top, True), (bottom, False)):
        if text:
            _stamp(draw, text, w, h, is_top)
    return img


async def _upload_sticker(client, chat_id: int, img: Image.Image, emoji: str = "🤔"):
    path = f"{TMP}/mmf_upload_{chat_id}.webp"
    _fit_512(img.convert("RGBA")).save(path, "WEBP", lossless=True, quality=100, method=6)
    try:
        media = await client.invoke(raw.functions.messages.UploadMedia(
            peer=await client.resolve_peer(chat_id),
            media=raw.types.InputMediaUploadedDocument(
                mime_type="image/webp",
                file=await client.save_file(path),
                attributes=[
                    raw.types.DocumentAttributeFilename(file_name="sticker.webp"),
                    raw.types.DocumentAttributeSticker(alt=emoji, stickerset=raw.types.InputStickerSetEmpty()),
                ],
            ),
        ))
        doc = media.document
        await client.invoke(raw.functions.messages.SendMedia(
            peer=await client.resolve_peer(chat_id),
            media=raw.types.InputMediaDocument(id=raw.types.InputDocument(
                id=doc.id, access_hash=doc.access_hash, file_reference=doc.file_reference,
            )),
            message="",
            random_id=client.rnd_id(),
        ))
    finally:
        _cleanup(path)


async def _get_pack(client, uid: int, fname: str, bot_username: str, sticker) -> str | None:
    packname, packnum = f"f{uid}_by_{bot_username}", 0
    for _ in range(50):
        stickerset = await get_sticker_set_by_name(client, packname)
        if not stickerset:
            await create_sticker_set(client, uid, f"{fname}'s kang pack", packname, [sticker])
            return packname
        if stickerset.set.count < MAX_STICKERS:
            try:
                await add_sticker_to_set(client, stickerset, sticker)
                return packname
            except StickerEmojiInvalid:
                return None
        packnum += 1
        packname = f"f{packnum}_{uid}_by_{bot_username}"
    return None


@app.on_message(filters.command("mmf"))
@capture_err
async def mmf(client, message: Message):
    r = message.reply_to_message
    if not r or not r.sticker:
        return await message.reply("reply to a sticker.\nusage: /mmf top text | bottom text")
    if r.sticker.is_animated or r.sticker.is_video:
        return await message.reply("only static stickers are supported.")

    top, _, bottom = " ".join(message.text.split()[1:]).partition("|")
    top, bottom = top.strip(), bottom.strip()
    if not top and not bottom:
        return await message.reply("usage: /mmf top text | bottom text")

    m = await message.reply("generating...")
    tmp = None
    try:
        tmp = await app.download_media(r.sticker)
        await _upload_sticker(client, message.chat.id, _render(tmp, top, bottom), r.sticker.emoji or "🤔")
        await m.delete()
    except Exception as e:
        await m.edit(f"error: {e}")
        print(format_exc())
    finally:
        _cleanup(tmp)


@app.on_message(filters.command("get_sticker"))
@capture_err
async def get_sticker(_, message: Message):
    r = message.reply_to_message
    if not r or not r.sticker:
        return await message.reply("reply to a sticker.")
    m = await message.reply("sending...")
    f = await r.download(f"{r.sticker.file_unique_id}.png")
    await gather(message.reply_photo(f), message.reply_document(f))
    await m.delete()
    _cleanup(f)


@app.on_message(filters.command("stickerinfo"))
@capture_err
async def sticker_info(_, message: Message):
    r = message.reply_to_message
    if not r or not r.sticker:
        return await message.reply("reply to a sticker.")
    s = r.sticker
    kind = "animated" if s.is_animated else "video" if s.is_video else "static"
    await message.reply(
        f"file id: <code>{s.file_id}</code>\n"
        f"emoji: {s.emoji or 'none'}\n"
        f"type: {kind}\n"
        f"set: <code>{s.set_name or 'none'}</code>\n"
        f"size: {s.file_size} bytes\n"
        f"dimensions: {s.width}x{s.height}",
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_message(filters.command("delsticker"))
@capture_err
async def del_sticker(client, message: Message):
    r = message.reply_to_message
    if not r or not r.sticker:
        return await message.reply("reply to a sticker to delete it from its pack.")
    m = await message.reply("deleting...")
    try:
        decoded = FileId.decode(r.sticker.file_id)
        doc = raw.types.InputDocument(id=decoded.media_id, access_hash=decoded.access_hash, file_reference=decoded.file_reference)
        await remove_sticker_from_set(client, doc)
        await m.edit("sticker deleted from pack.")
    except Exception as e:
        await m.edit(f"failed: {e}")


async def _kang_sticker(client, message: Message):
    replied = message.reply_to_message
    emoji = message.text.split()[1:2] or [replied.sticker.emoji if replied.sticker and replied.sticker.emoji else "🤔"]
    emoji = emoji[0]

    if replied.sticker:
        return await create_sticker(await get_document_from_file_id(replied.sticker.file_id), emoji), None

    doc = replied.photo or replied.document
    if not doc:
        raise ValueError("cannot kang this message type.")
    if doc.file_size and doc.file_size > 10_000_000:
        raise ValueError("file size too large (max 10MB).")

    tmp = await app.download_media(doc)
    if not tmp or not os.path.exists(tmp):
        raise ValueError("failed to download file.")

    ext = tmp.rsplit(".", 1)[-1].lower()
    if ext not in ALL_TYPES:
        _cleanup(tmp)
        raise ValueError(f"format not supported.\nstatic: {', '.join(sorted(STATIC_TYPES))}\nanimated: tgs | video: webm")

    animated, video = detect_sticker_type(tmp)
    if not animated and not video and ext != "png":
        png = _to_png(tmp)
        _cleanup(tmp if png != tmp else None)
        tmp = png

    sticker = await create_sticker(await upload_document(client, tmp, message.chat.id), emoji)
    return sticker, tmp


@app.on_message(filters.command("kang"))
@capture_err
async def kang(client, message: Message):
    if not message.reply_to_message:
        return await message.reply("reply to a sticker or image to kang.")
    if not message.from_user:
        return await message.reply("anon admin, kang stickers in my pm.")

    m = await message.reply("kanging...")
    tmp = None
    try:
        sticker, tmp = await _kang_sticker(client, message)
    except ValueError as e:
        return await m.edit(str(e))
    except ShortnameOccupyFailed:
        return await m.edit("change your name or username and try again.")
    except Exception as e:
        await m.edit(f"error: {e}")
        print(format_exc())
        return
    finally:
        _cleanup(tmp)

    uid, fname = message.from_user.id, message.from_user.first_name[:32]
    bot_username = (await client.get_me()).username

    try:
        packname = await _get_pack(client, uid, fname, bot_username, sticker)
        if not packname:
            return await m.edit("invalid emoji or too many packs.")
        await m.edit(
            "sticker kanged!\ntap below to open your pack",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("View Pack", url=f"https://t.me/addstickers/{packname}")]]),
        )
    except (PeerIdInvalid, UserIsBlocked):
        await m.edit(
            "start a private chat with me first!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Start Bot", url=f"https://t.me/{bot_username}")]]),
        )
    except StickerPngNopng:
        await m.edit("sticker must be a png file.")
    except StickerPngDimensions:
        await m.edit("invalid sticker dimensions.")
    except Exception as e:
        await m.edit(f"unexpected error: {e}")
        print(format_exc())
