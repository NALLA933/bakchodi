from pyrogram import types, enums
from pyrogram.errors import RPCError, QueryIdInvalid
from anony import app, config

@app.on_guest_message()
async def _guest_message(_, message: types.Message):
    caller = message.from_user or message.sender_chat
    name = getattr(caller, "first_name", None) or getattr(caller, "title", "there")

    html = f"""
<video src="{config.START_ANIMATION}"/>
<h1>🎧 {app.name}</h1>
<p>Hey {name}! I stream music straight into your voice chats.</p>
<hr/>
<table bordered>
<tr><th>Command</th><th>Description</th></tr>
<tr><td><code>/play</code></td><td>Start streaming</td></tr>
<tr><td><code>/skip</code></td><td>Skip current track</td></tr>
<tr><td><code>/queue</code></td><td>View queue</td></tr>
<tr><td><code>/loop</code></td><td>Repeat mode</td></tr>
</table>
<footer>💡 Add me to your group and just type /play</footer>
"""

    reply_markup = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("➕ Add to group", url=f"https://t.me/{app.username}?startgroup=true", style=enums.ButtonStyle.SUCCESS)],
        [
            types.InlineKeyboardButton("🎵 Play", url=f"https://t.me/{app.username}?start=help", style=enums.ButtonStyle.PRIMARY),
            types.InlineKeyboardButton("💬 Chat", url=f"https://t.me/{app.username}", style=enums.ButtonStyle.PRIMARY),
        ],
    ])

    rich_message = types.InputRichMessage(html=html)

    result = types.InlineQueryResultArticle(
        id="guest_reply",
        title=f"{app.name} — Music Bot",
        description="Stream music in your groups & channels",
        thumb_url=config.START_IMG,
        input_message_content=types.InputRichMessageContent(rich_message=rich_message),
        reply_markup=reply_markup,
    )

    try:
        await app.answer_guest_query(guest_query_id=message.guest_query_id, result=result)
    except QueryIdInvalid:
        pass
    except RPCError as e:
        print(e)