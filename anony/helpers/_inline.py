from pyrogram import types, Client, filters
from pyrogram.enums import ButtonStyle
from pyrogram.types import CallbackQuery

from anony import app, config, lang
from anony.core.lang import lang_codes



_HELP_KEYS = {
    "admins": 0,
    "auth": 1,
    "blist": 2,
    "lang": 3,
    "ping": 4,
    "play": 5,
    "queue": 6,
    "stats": 7,
    "sudo": 8,
    "kang": 10,
}
_HELP_CBS = list(_HELP_KEYS.keys())
_HELP_PAGE_SIZE = 8


_HELP_ICONS = {
    "admins": "@",
    "auth": "&",
    "blist": "!",
    "lang": "~",
    "ping": "o",
    "play": ">",
    "queue": "=",
    "stats": "%",
    "sudo": "$",
    "kang": "+",
}

ICONS = {
    "back": "<<",
    "next": ">>",
    "close": "x",
    "add": "+",
    "replay": "|<<",
    "resume": ">",
    "pause": "||",
    "skip": ">>|",
    "stop": "[]",
    "copy": "[c]",
    "open": "[->]",
    "selected": "[x]",
    "arrow": "->",
}


class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = types.InlineKeyboardButton
        self.register_callbacks()

    def register_callbacks(self):
        @app.on_callback_query(filters.regex("^controls status"))
        async def status_noop(client: Client, callback_query: CallbackQuery):
            await callback_query.answer()

    def _btn(
        self,
        text: str,
        callback_data: str,
        style: ButtonStyle = ButtonStyle.PRIMARY,
    ) -> types.InlineKeyboardButton:
        return self.ikb(text=text, callback_data=callback_data, style=style)

    def _url_btn(
        self,
        text: str,
        url: str,
        style: ButtonStyle = ButtonStyle.PRIMARY,
    ) -> types.InlineKeyboardButton:
        return self.ikb(text=text, url=url, style=style)

    def cancel_dl(self, text: str) -> types.InlineKeyboardMarkup:
        return self.ikm([
            [self._btn(f"{ICONS['close']}  {text}", "cancel_dl", ButtonStyle.DANGER)]
        ])

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
    ) -> types.InlineKeyboardMarkup:

        keyboard = []

        label = status or timer
        if label:
            keyboard.append(
                [self._btn(label, f"controls status {chat_id}", ButtonStyle.PRIMARY)]
            )

        if not remove:
            keyboard.append([
                self._btn(ICONS["replay"], f"controls replay {chat_id}", ButtonStyle.PRIMARY),
                self._btn(ICONS["resume"], f"controls resume {chat_id}", ButtonStyle.SUCCESS),
                self._btn(ICONS["pause"], f"controls pause {chat_id}", ButtonStyle.PRIMARY),
                self._btn(ICONS["skip"], f"controls skip {chat_id}", ButtonStyle.PRIMARY),
                self._btn(ICONS["stop"], f"controls stop {chat_id}", ButtonStyle.DANGER),
            ])

        return self.ikm(keyboard)

    def help_markup(
        self,
        _lang: dict,
        back: bool = False,
        page: int = 0,
    ) -> types.InlineKeyboardMarkup:

        if back:
            rows = [[
                self._btn(f"{ICONS['back']} {_lang['back']}", "help back", ButtonStyle.SUCCESS),
                self._btn(f"{ICONS['close']} {_lang['close']}", "help close", ButtonStyle.DANGER),
            ]]
            return self.ikm(rows)

        total_pages = (len(_HELP_CBS) + _HELP_PAGE_SIZE - 1) // _HELP_PAGE_SIZE
        start = page * _HELP_PAGE_SIZE
        page_cbs = _HELP_CBS[start:start + _HELP_PAGE_SIZE]

        buttons = [
            self._btn(
                f"{_HELP_ICONS[cb]}  {_lang[f'help_{_HELP_KEYS[cb]}']}",
                f"help {cb}",
                ButtonStyle.PRIMARY,
            )
            for cb in page_cbs
        ]
        
        rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

        nav = []
        if page > 0:
            nav.append(self._btn(f"{ICONS['back']} {_lang['prev']}", f"help page {page - 1}", ButtonStyle.SUCCESS))
        if page < total_pages - 1:
            nav.append(self._btn(f"{_lang['next']} {ICONS['next']}", f"help page {page + 1}", ButtonStyle.SUCCESS))
        if nav:
            rows.append(nav)

        rows.append([self._btn(f"{ICONS['close']} {_lang['close']}", "help close", ButtonStyle.DANGER)])

        return self.ikm(rows)

    def lang_markup(self, _lang: str) -> types.InlineKeyboardMarkup:
        langs = lang.get_languages()

        buttons = [
            self.ikb(
                text=f"{ICONS['selected'] + ' ' if code == _lang else ''}{name} ({code})",
                callback_data=f"lang_change {code}",
                style=ButtonStyle.SUCCESS if code == _lang else ButtonStyle.PRIMARY,
            )
            for code, name in langs.items()
        ]

        rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        return self.ikm(rows)

    def ping_markup(self, text: str) -> types.InlineKeyboardMarkup:
        return self.ikm([
            [self._url_btn(text, config.SUPPORT_CHAT, ButtonStyle.PRIMARY)]
        ])

    def play_queued(
        self,
        chat_id: int,
        item_id: str,
        _text: str
    ) -> types.InlineKeyboardMarkup:

        return self.ikm([
            [self._btn(_text, f"controls force {chat_id} {item_id}", ButtonStyle.PRIMARY)]
        ])

    def queue_markup(
        self,
        chat_id: int,
        _text: str,
        playing: bool
    ) -> types.InlineKeyboardMarkup:

        action = "pause" if playing else "resume"
        icon = ICONS["pause"] if playing else ICONS["resume"]
        style = ButtonStyle.DANGER if playing else ButtonStyle.SUCCESS

        return self.ikm([
            [self._btn(f"{icon} {_text}", f"controls {action} {chat_id} q", style)]
        ])

    def settings_markup(
        self,
        lang: dict,
        admin_only: bool,
        cmd_delete: bool,
        language: str,
        chat_id: int,
    ) -> types.InlineKeyboardMarkup:

        return self.ikm([
            [
                self._btn(f"{lang['play_mode']} {ICONS['arrow']}", "settings", ButtonStyle.PRIMARY),
                self._btn(str(admin_only), "settings play", ButtonStyle.SUCCESS if admin_only else ButtonStyle.DANGER),
            ],
            [
                self._btn(f"{lang['cmd_delete']} {ICONS['arrow']}", "settings", ButtonStyle.PRIMARY),
                self._btn(str(cmd_delete), "settings delete", ButtonStyle.SUCCESS if cmd_delete else ButtonStyle.DANGER),
            ],
            [
                self._btn(f"{lang['language']} {ICONS['arrow']}", "settings", ButtonStyle.PRIMARY),
                self._btn(lang_codes[language], "language", ButtonStyle.PRIMARY),
            ],
        ])

    def start_key(
        self,
        lang: dict,
        private: bool = False
    ) -> types.InlineKeyboardMarkup:

        return self.ikm([
            [
                self._url_btn(
                    f"{ICONS['add']} {lang['add_me']}",
                    f"https://t.me/{app.username}?startgroup=true",
                    ButtonStyle.SUCCESS,
                )
            ],
            [
                self._btn(lang["help"], "help", ButtonStyle.PRIMARY),
                self._btn(lang["language"], "language", ButtonStyle.PRIMARY),
            ],
            [
                self._url_btn(lang["support"], config.SUPPORT_CHAT, ButtonStyle.PRIMARY),
                self._url_btn(lang["channel"], config.SUPPORT_CHANNEL, ButtonStyle.PRIMARY),
            ],
            [
                self._url_btn("Owner", "https://t.me/I_shadwoo", ButtonStyle.PRIMARY),
            ],
        ])

    def yt_key(self, link: str) -> types.InlineKeyboardMarkup:
        return self.ikm([
            [
                self.ikb(text=f"{ICONS['copy']} Copy", copy_text=link, style=ButtonStyle.PRIMARY),
                self.ikb(text=f"{ICONS['open']} Open", url=link, style=ButtonStyle.SUCCESS),
            ]
        ])