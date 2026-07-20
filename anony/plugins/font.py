import html as html_module
from pyrogram import filters, enums
from pyrogram.enums import ButtonStyle, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from pyrogram.errors import MessageNotModified, QueryIdInvalid, MessageIdInvalid

from anony import app

original_texts: dict[int, str] = {}


class Fonts:
    @staticmethod
    def _tr(text, normal, mapped):
        return text.translate(str.maketrans(normal, mapped))

    @staticmethod
    def _deco(text, *chars):
        return "".join(c + "".join(chars) if c.isalpha() else c for c in text)

    N = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

    @classmethod
    def typewriter(cls, t): return cls._tr(t, cls.N, "𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣")
    @classmethod
    def outline(cls, t): return cls._tr(t, cls.N, "𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫")
    @classmethod
    def serief(cls, t): return cls._tr(t, cls.N, "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳")
    @classmethod
    def bold_cool(cls, t): return cls._tr(t, cls.N, "𝑨𝑩𝑪𝑫𝑬𝑭𝑮𝑯𝑰𝑱𝑲𝑳𝑴𝑵𝑶𝑷𝑸𝑹𝑺𝑻𝑼𝑽𝑾𝑿𝒀𝒁𝒂𝒃𝒄𝒅𝒆𝒇𝒈𝒉𝒊𝒋𝒌𝒍𝒎𝒏𝒐𝒑𝒒𝒓𝒔𝒕𝒖𝒗𝒘𝒙𝒚𝒛")
    @classmethod
    def cool(cls, t): return cls._tr(t, cls.N, "𝐴𝐵𝐶𝐷𝐸𝐹𝐺𝐻𝐼𝐽𝐾𝐿𝑀𝑁𝑂𝑃𝑄𝑅𝑆𝑇𝑈𝑉𝑊𝑋𝑌𝑍𝑎𝑏𝑐𝑑𝑒𝑓𝑔ℎ𝑖𝑗𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧")
    @classmethod
    def smallcap(cls, t): return cls._tr(t, cls.N, "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ")
    @classmethod
    def script(cls, t): return cls._tr(t, cls.N, "𝒜𝐵𝒞𝒟𝐸𝐹𝒢𝐻𝐼𝒥𝒦𝐿𝑀𝒩𝒪𝒫𝒬𝑅𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵𝒶𝒷𝒸𝒹𝑒𝒻𝑔𝒽𝒾𝒿𝓀𝓁𝓂𝓃𝑜𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏")
    @classmethod
    def bold_script(cls, t): return cls._tr(t, cls.N, "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃")
    @classmethod
    def tiny(cls, t): return cls._tr(t, cls.N, "ᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾQᴿˢᴛᵁⱽᵂˣʸᶻᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖᑫʳˢᵗᵘᵛʷˣʸᶻ")
    @classmethod
    def comic(cls, t): return cls._tr(t, cls.N, "ᗩᗷᑕᗪEᖴGᕼIᒍKᒪᗰᑎOᑭᑫᖇᔕTᑌᐯᗯ᙭YᘔᗩᗷᑕᗪEᖴGᕼIᒍKᒪᗰᑎOᑭᑫᖇᔕTᑌᐯᗯ᙭Yᘔ")
    @classmethod
    def san(cls, t): return cls._tr(t, cls.N, "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇")
    @classmethod
    def slant_san(cls, t): return cls._tr(t, cls.N, "𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕𝙖𝙗𝙘𝙙𝙚𝙛𝙜𝙝𝙞𝙟𝙠𝙡𝙢𝙣𝙤𝙥𝙦𝙧𝙨𝙩𝙪𝙫𝙬𝙭𝙮𝙯")
    @classmethod
    def slant(cls, t): return cls._tr(t, cls.N, "𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻")
    @classmethod
    def sim(cls, t): return cls._tr(t, cls.N, "𝖠𝖡𝖢𝖣𝖤𝖥𝖦𝖧𝖨𝖩𝖪𝖫𝖬𝖭𝖮𝖯𝖰𝖱𝖲𝖳𝖴𝖵𝖶𝖷𝖸𝖹𝖺𝖻𝖼𝖽𝖾𝖿𝗀𝗁𝗂𝗃𝗄𝗅𝗆𝗇𝗈𝗉𝗊𝗋𝗌𝗍𝗎𝗏𝗐𝗑𝗒𝗓")
    @classmethod
    def circles(cls, t): return cls._tr(t, cls.N, "ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ")
    @classmethod
    def dark_circle(cls, t): return cls._tr(t, cls.N, "🅐🅑🅒🅓🅔🅕🅖🅗🅘🅙🅚🅛🅜🅝🅞🅟🅠🅡🅢🅣🅤🅥🅦🅧🅨🅩🅐🅑🅒🅓🅔🅕🅖🅗🅘🅙🅚🅛🅜🅝🅞🅟🅠🅡🅢🅣🅤🅥🅦🅧🅨🅩")
    @classmethod
    def gothic(cls, t): return cls._tr(t, cls.N, "𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷")
    @classmethod
    def bold_gothic(cls, t): return cls._tr(t, cls.N, "𝕬𝕭𝕮𝕯𝕰𝕱𝕲𝕳𝕴𝕵𝕶𝕷𝕸𝕹𝕺𝕻𝕼𝕽𝕾𝕿𝖀𝖁𝖂𝖃𝖄𝖅𝖆𝖇𝖈𝖉𝖊𝖋𝖌𝖍𝖎𝖏𝖐𝖑𝖒𝖓𝖔𝖕𝖖𝖗𝖘𝖙𝖚𝖛𝖜𝖝𝖞𝖟")
    @classmethod
    def special(cls, t):
        chars = "🇦 🇧 🇨 🇩 🇪 🇫 🇬 🇭 🇮 🇯 🇰 🇱 🇲 🇳 🇴 🇵 🇶 🇷 🇸 🇹 🇺 🇻 🇼 🇽 🇾 🇿 🇦 🇧 🇨 🇩 🇪 🇫 🇬 🇭 🇮 🇯 🇰 🇱 🇲 🇳 🇴 🇵 🇶 🇷 🇸 🇹 🇺 🇻 🇼 🇽 🇾 🇿".split()
        return t.translate({ord(c): chars[i] for i, c in enumerate(cls.N)})
    @classmethod
    def square(cls, t): return cls._tr(t, cls.N, "🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉")
    @classmethod
    def dark_square(cls, t): return cls._tr(t, cls.N, "🅰︎🅱︎🅲︎🅳︎🅴︎🅵︎🅶︎🅷︎🅸︎🅹︎🅺︎🅻︎🅼︎🅽︎🅾︎🅿︎🆀︎🆁︎🆂︎🆃︎🆄︎🆅︎🆆︎🆇︎🆈︎🆉︎🅰︎🅱︎🅲︎🅳︎🅴︎🅵︎🅶︎🅷︎🅸︎🅹︎🅺︎🅻︎🅼︎🅽︎🅾︎🅿︎🆀︎🆁︎🆂︎🆃︎🆄︎🆅︎🆆︎🆇︎🆈︎🆉︎")
    @classmethod
    def andalucia(cls, t): return cls._tr(t, cls.N, "ꪖ᥇ᥴᦔꫀᠻᧁꫝ꠸꠫ҡꪶꪑꪀꪮρꫀꪹకꪻꪊꪜ᭙᥊ꪗɀꪖ᥇ᥴᦔꫀᠻᧁꫝ꠸꠫ҡꪶꪑꪀꪮρꫀꪹకꪻꪊꪜ᭙᥊ꪗɀ")
    @classmethod
    def manga(cls, t): return cls._tr(t, cls.N, "ﾑ乃ᄃり乇ｷムんﾉﾌズﾚﾶ刀のｱゐ尺丂ｲひ√Wﾒﾘ乙ﾑ乃ᄃり乇ｷムんﾉﾌズﾚﾶ刀のｱゐ尺丂ｲひ√Wﾒﾘ乙")
    @classmethod
    def ladybug(cls, t): return cls._tr(t, cls.N, "ꍏꌃꉓꀸꍟꎇꁅꃅꀤꀭꀘ꒒ꂵꈤꂦᖘꆰꋪꌗ꓄ꀎꅏꅏꊼꌩꁴꍏꌃꉓꀸꍟꎇꁅꃅꀤꀭꀘ꒒ꂵꈤꂦᖘꆰꋪꌗ꓄ꀎꅏꅏꊼꌩꁴ")
    @classmethod
    def rvnes(cls, t): return cls._tr(t, cls.N, "ልጌርዕቿቻኗዘጎጋጕረጠክዐየዒዪነፕሁሀሠሸሃጊልጌርዕቿቻኗዘጎጋጕረጠክዐየዒዪነፕሁሀሠሸሃጊ")

    @classmethod
    def cloud(cls, t): return cls._deco(t, "\u0356", "\u0361")
    @classmethod
    def happy(cls, t): return cls._deco(t, "\u0306", "\u0308")
    @classmethod
    def sad(cls, t): return cls._deco(t, "\u0351", "\u0308")
    @classmethod
    def stinky(cls, t): return cls._deco(t, "\u033E")
    @classmethod
    def bubbles(cls, t): return cls._deco(t, "\u0365", "\u0366")
    @classmethod
    def underline(cls, t): return cls._deco(t, "\u035F")
    @classmethod
    def rays(cls, t): return cls._deco(t, "\u0489")
    @classmethod
    def birds(cls, t): return cls._deco(t, "\u0488")
    @classmethod
    def slash(cls, t): return cls._deco(t, "\u0338")
    @classmethod
    def stop(cls, t): return cls._deco(t, "\u20E0")
    @classmethod
    def skyline(cls, t): return cls._deco(t, "\u033A", "\u0346")
    @classmethod
    def arrows(cls, t): return cls._deco(t, "\u030E")
    @classmethod
    def strike(cls, t): return cls._deco(t, "\u0336")
    @classmethod
    def frozen(cls, t): return cls._deco(t, "\u0F99")


FONT_MAP = {
    "typewriter": Fonts.typewriter, "outline": Fonts.outline, "serif": Fonts.serief,
    "bold_cool": Fonts.bold_cool, "cool": Fonts.cool, "small_cap": Fonts.smallcap,
    "script": Fonts.script, "script_bolt": Fonts.bold_script, "tiny": Fonts.tiny,
    "comic": Fonts.comic, "sans": Fonts.san, "slant_sans": Fonts.slant_san,
    "slant": Fonts.slant, "sim": Fonts.sim, "circles": Fonts.circles,
    "circle_dark": Fonts.dark_circle, "gothic": Fonts.gothic, "gothic_bolt": Fonts.bold_gothic,
    "cloud": Fonts.cloud, "happy": Fonts.happy, "sad": Fonts.sad,
    "special": Fonts.special, "squares": Fonts.square, "squares_bold": Fonts.dark_square,
    "andalucia": Fonts.andalucia, "manga": Fonts.manga, "stinky": Fonts.stinky,
    "bubbles": Fonts.bubbles, "underline": Fonts.underline, "ladybug": Fonts.ladybug,
    "rays": Fonts.rays, "birds": Fonts.birds, "slash": Fonts.slash,
    "stop": Fonts.stop, "skyline": Fonts.skyline, "arrows": Fonts.arrows,
    "qvnes": Fonts.rvnes, "strike": Fonts.strike, "frozen": Fonts.frozen,
}


def btn(text, data, style=ButtonStyle.PRIMARY):
    return InlineKeyboardButton(text=text, callback_data=data, style=style)


def get_main_buttons():
    return InlineKeyboardMarkup([
        [btn("𝚃𝚢𝚙𝚎𝚠𝚛𝚒𝚝𝚎𝚛", "style+typewriter"), btn("𝕆𝕦𝕥𝕝𝕚𝕟𝕖", "style+outline"), btn("𝐒𝐞𝐫𝐢𝐟", "style+serif")],
        [btn("𝑺𝒆𝒓𝒊𝒇", "style+bold_cool"), btn("𝑆𝑒𝑟𝑖𝑓", "style+cool"), btn("Sᴍᴀʟʟ Cᴀᴘs", "style+small_cap")],
        [btn("𝓈𝒸𝓇𝒾𝓅𝓉", "style+script"), btn("𝓼𝓬𝓻𝓲𝓹𝓽", "style+script_bolt"), btn("ᵗⁱⁿʸ", "style+tiny")],
        [btn("ᑕOᗰIᑕ", "style+comic"), btn("𝗦𝗮𝗻𝘀", "style+sans"), btn("𝙎𝙖𝙣𝙨", "style+slant_sans")],
        [btn("𝘚𝘢𝘯𝘴", "style+slant"), btn("𝖲𝖺𝗇𝗌", "style+sim"), btn("Ⓒ︎Ⓘ︎Ⓡ︎Ⓒ︎Ⓛ︎Ⓔ︎Ⓢ︎", "style+circles")],
        [btn("🅒︎🅘︎🅡︎🅒︎🅛︎🅔︎🅢︎", "style+circle_dark"), btn("𝔊𝔬𝔱𝔥𝔦𝔠", "style+gothic"), btn("𝕲𝖔𝖙𝖍𝖎𝖈", "style+gothic_bolt")],
        [btn("C͜͡l͜͡o͜͡u͜͡d͜͡s͜͡", "style+cloud"), btn("H̆̈ă̈p̆̈p̆̈y̆̈", "style+happy"), btn("S̑̈ȃ̈d̑̈", "style+sad")],
        [btn("Close", "close_reply", ButtonStyle.DANGER), btn("Next", "nxt", ButtonStyle.SUCCESS)],
    ])


def get_next_buttons():
    return InlineKeyboardMarkup([
        [btn("🇸 🇵 🇪 🇨 🇮 🇦 🇱", "style+special"), btn("🅂🅀🅄🄰🅁🄴🅂", "style+squares"), btn("🆂︎🆀︎🆄︎🅰︎🆁︎🅴︎🆂︎", "style+squares_bold")],
        [btn("ꪖꪀᦔꪖꪶꪊᥴ𝓲ꪖ", "style+andalucia"), btn("爪卂几ᘜ卂", "style+manga"), btn("S̾t̾i̾n̾k̾y̾", "style+stinky")],
        [btn("B̥ͦu̥ͦb̥ͦb̥ͦl̥ͦe̥ͦs̥ͦ", "style+bubbles"), btn("U͟n͟d͟e͟r͟l͟i͟n͟e͟", "style+underline"), btn("꒒ꍏꀷꌩꌃꀎꁅ", "style+ladybug")],
        [btn("R҉a҉y҉s҉", "style+rays"), btn("B҈i҈r҈d҈s҈", "style+birds"), btn("S̸l̸a̸s̸h̸", "style+slash")],
        [btn("s⃠t⃠o⃠p⃠", "style+stop"), btn("S̺͆k̺͆y̺͆l̺͆i̺͆n̺͆e̺͆", "style+skyline"), btn("A͎r͎r͎o͎w͎s͎", "style+arrows")],
        [btn("ዪሀክቿነ", "style+qvnes"), btn("S̶t̶r̶i̶k̶e̶", "style+strike"), btn("F༙r༙o༙z༙e༙n༙", "style+frozen")],
        [btn("Close", "close_reply", ButtonStyle.DANGER), btn("Back", "nxt+0", ButtonStyle.SUCCESS)],
    ])


@app.on_message(filters.command(["font", "fonts"]))
async def style_buttons(_, message: Message):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        return await message.reply_text(
            "<b>Usage:</b> <code>/font your_text</code>",
            parse_mode=ParseMode.HTML,
            quote=True
        )

    text = parts[1]
    sent = await message.reply_text(
        f"<code>{html_module.escape(text)}</code>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_buttons(),
        quote=True
    )
    original_texts[sent.id] = text


@app.on_callback_query(filters.regex("^nxt$"))
async def next_fonts(_, cb: CallbackQuery):
    try:
        await cb.answer()
        await cb.message.edit_reply_markup(get_next_buttons())
    except (QueryIdInvalid, MessageNotModified, MessageIdInvalid):
        pass


@app.on_callback_query(filters.regex(r"^nxt\+0$"))
async def back_fonts(_, cb: CallbackQuery):
    try:
        await cb.answer()
        await cb.message.edit_reply_markup(get_main_buttons())
    except (QueryIdInvalid, MessageNotModified, MessageIdInvalid):
        pass


@app.on_callback_query(filters.regex("^close_reply$"))
async def close_reply(_, cb: CallbackQuery):
    try:
        await cb.answer()
        original_texts.pop(cb.message.id, None)
        await cb.message.delete()
    except (QueryIdInvalid, MessageIdInvalid):
        pass


@app.on_callback_query(filters.regex("^style\\+"))
async def apply_style(_, cb: CallbackQuery):
    try:
        await cb.answer()
        key = cb.data.split("+", 1)[1]
        font_func = FONT_MAP.get(key)
        if not font_func:
            return await cb.answer("Unknown style.", show_alert=True)

        text = original_texts.get(cb.message.id)
        if not text:
            try:
                text = cb.message.reply_to_message.text.split(None, 1)[1]
            except (AttributeError, IndexError):
                return await cb.answer("Original text not found.", show_alert=True)

        styled = html_module.escape(font_func(text))
        await cb.message.edit_text(
            f"<code>{styled}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=cb.message.reply_markup
        )
    except MessageNotModified:
        pass
    except QueryIdInvalid:
        pass
    except MessageIdInvalid:
        pass
    except Exception as e:
        try:
            await cb.answer(f"Error: {e}", show_alert=True)
        except QueryIdInvalid:
            pass