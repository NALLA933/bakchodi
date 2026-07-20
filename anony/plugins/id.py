from pyrogram import filters
from pyrogram.types import Message
from anony import app

PREFIXES = ["!", "/", "."]


def multi_prefix(cmd: str):
    async def func(flt, client, message):
        return message.text and any(message.text.startswith(p + cmd) for p in PREFIXES)
    return filters.create(func)


def format_user(user, prefix: str = "") -> str:
    if user.is_deleted:
        return f"{prefix}Deleted Account\nID: <code>{user.id}</code>"

    name = user.first_name or "Unknown"
    info = f"{prefix}<code>{name}</code>\nID: <code>{user.id}</code>"

    if user.username:
        info += f"\nUsername: <code>@{user.username}</code>"
    else:
        info += f"\nMention: {user.mention}"

    flags = []
    if user.is_bot:
        flags.append("Bot")
    if user.is_premium:
        flags.append("Premium")
    if user.is_verified:
        flags.append("Verified")
    if user.is_scam:
        flags.append("Scam")
    if user.is_fake:
        flags.append("Fake")

    if flags:
        info += "\n" + " | ".join(flags)

    return info


def format_chat(chat, prefix: str = "") -> str:
    name = chat.title or chat.first_name or "Unknown"
    info = f"{prefix}<code>{name}</code>\nID: <code>{chat.id}</code>"

    if chat.username:
        info += f"\nUsername: <code>@{chat.username}</code>"
    if hasattr(chat, 'members_count'):
        info += f"\nMembers: {chat.members_count}"

    return info


@app.on_message(multi_prefix("id") & ~app.bl_users)
async def id_handler(_, m: Message):
    reply = m.reply_to_message
    args = m.text.split(maxsplit=1)
    parts = []

    if reply:
        if reply.from_user:
            parts.append(format_user(reply.from_user))

        if reply.sender_chat:
            parts.append(format_chat(reply.sender_chat, "Sender: "))

        if reply.forward_from:
            parts.append(format_user(reply.forward_from, "Forward: "))

        if reply.forward_from_chat:
            parts.append(format_chat(reply.forward_from_chat, "Forward Chat: "))

        if reply.forward_sender_name:
            parts.append(f"Forward: <code>{reply.forward_sender_name}</code>\nHidden Account")

        if reply.contact:
            contact = reply.contact
            contact_info = f"Contact: <code>{contact.first_name or 'Unknown'}</code>"
            if contact.last_name:
                contact_info += f" <code>{contact.last_name}</code>"
            contact_info += f"\nPhone: <code>{contact.phone_number}</code>"
            if contact.user_id:
                contact_info += f"\nUser ID: <code>{contact.user_id}</code>"
            parts.append(contact_info)

        if parts:
            return await m.reply_text("\n\n".join(parts))

    if len(args) > 1:
        target = args[1].strip()

        if target.startswith("@"):
            username = target.replace("@", "")
            try:
                user = await app.get_users(username)
                return await m.reply_text(format_user(user))
            except Exception:
                try:
                    chat = await app.get_chat(username)
                    return await m.reply_text(format_chat(chat))
                except Exception as e:
                    return await m.reply_text(f"<b>Failed to fetch:</b> <code>{e}</code>")

        if target.isdigit() or (target.startswith("-") and target[1:].isdigit()):
            try:
                user_id = int(target)
                try:
                    user = await app.get_users(user_id)
                    return await m.reply_text(format_user(user))
                except Exception:
                    try:
                        chat = await app.get_chat(user_id)
                        return await m.reply_text(format_chat(chat))
                    except Exception as e:
                        return await m.reply_text(f"<b>Failed to fetch ID:</b> <code>{e}</code>")
            except ValueError:
                return await m.reply_text("<b>Invalid ID format</b>")

        if m.entities:
            for entity in m.entities:
                if entity.type == "text_mention" and entity.user:
                    return await m.reply_text(format_user(entity.user))

        return await m.reply_text("<b>Invalid input.</b> Use username, ID, or mention a user")

    if m.entities:
        for entity in m.entities:
            if entity.type == "text_mention" and entity.user:
                return await m.reply_text(format_user(entity.user))

    if m.from_user:
        parts.append(format_user(m.from_user, "Your "))

    if m.sender_chat:
        parts.append(format_chat(m.sender_chat, "Sender: "))

    chat_name = m.chat.title or "Private"
    chat_info = f"Chat: <code>{chat_name}</code>\nChat ID: <code>{m.chat.id}</code>"
    if m.chat.username:
        chat_info += f"\nUsername: <code>@{m.chat.username}</code>"
    parts.append(chat_info)

    await m.reply_text("\n\n".join(parts))