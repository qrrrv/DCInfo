"""
⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀
⡀⢠⠋⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⢷⡀⡀
⢀⡟⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⢀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⢀⣤⠶⡀⡀⣷⡀
⢸⠁⡀⡀⡀⡀⡀⡀⣿⡇⡀⡀⡀⡀⡀⡀⢀⡿⠁⣠⡀⡀⣿⡀⡀⡀⣀⡴⠛⠁⡀⡀⡀⡀⢹⡀
⢸⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⣿⡀⡀⣿⡀⡀⣿⡀⡀⡀⠉⠳⣤⡀⡀⡀⡀⡀⢸⡀
⠘⣇⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⢀⡀⡀⢿⣤⣶⠹⣦⣴⠏⡀⡀⡀⡀⡀⡀⠈⠛⠦⡀⡀⣿⡀
⡀⠻⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⣰⠃⡀
⡀⡀⠁⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀

                                   Made by @JavaScript_XD
                                   Channel: https://t.me/plugin_XD
                                   Created: 30.10.2026
                                   Updated: 30.10.2026
"""

import html
import importlib
import logging
import re

from .. import loader, utils

logger = logging.getLogger(__name__)

DC_PLACES = {
    1: "Майами 🇺🇸",
    2: "Амстердам 🇳🇱",
    3: "Майами 🇺🇸",
    4: "Амстердам 🇳🇱",
    5: "Сингапур 🇸🇬",
}


def _import_tl():
    """Находит пакет Telethon-форка: у Heroku это herokutl, у Hikka — hikkatl."""
    for root in ("herokutl", "hikkatl", "telethon"):
        try:
            return (
                importlib.import_module(f"{root}.tl.functions.users"),
                importlib.import_module(f"{root}.tl.functions.channels"),
                importlib.import_module(f"{root}.tl.functions.messages"),
            )
        except ImportError:
            continue
    return None, None, None


_USERS, _CHANNELS, _MESSAGES = _import_tl()


def esc(value) -> str:
    return html.escape(str(value), quote=False)


@loader.tds
class DCInfo(loader.Module):
    """Показывает дата-центр (DC) аккаунта Telegram"""

    strings = {
        "name": "DCInfo",
        "_cls_doc": "Показывает дата-центр (DC) аккаунта Telegram",
        "_cmd_doc_dc": "[ответом на сообщение | @username | ID] — показать DC аккаунта",
        "searching": "🔍 <b>Определяю DC...</b>",
        "not_found": (
            "🚫 <b>Не нашёл аккаунт:</b> <code>{}</code>\n"
            "Для числового ID нужен общий чат или контакт — лучше используй @username."
        ),
        "result": "🌐 <b>Дата-центр:</b> <code>DC{dc}</code> · {place}\n{icon} {who}\n🆔 <code>{id}</code>",
        "no_dc": (
            "🤷 <b>DC определить не удалось</b>\n{icon} {who}\n🆔 <code>{id}</code>\n\n"
            "<i>Telegram отдаёт DC только через фото профиля. Если фото нет или оно скрыто "
            "настройками приватности — узнать DC нельзя.</i>"
        ),
    }

    @loader.command()
    async def dc(self, message):
        """[ответом на сообщение | @username | ID] — показать DC аккаунта"""
        client = message.client
        args = utils.get_args_raw(message).strip()
        reply = await message.get_reply_message()

        status = await utils.answer(message, self.strings("searching"))
        if isinstance(status, (list, tuple)):
            status = status[0]

        entity = None
        try:
            if args:
                entity = await self._resolve(client, args)
            elif reply:
                entity = await reply.get_sender() or await reply.get_chat()
            else:
                entity = await client.get_me()
        except Exception:
            logger.debug("DCInfo: не удалось получить аккаунт", exc_info=True)

        if entity is None:
            await utils.answer(status, self.strings("not_found").format(esc(args or "ответ")))
            return

        dc = await self._find_dc(client, entity)
        icon, who = self._describe(entity)
        entity_id = getattr(entity, "id", "?")

        if dc:
            text = self.strings("result").format(
                dc=dc,
                place=DC_PLACES.get(dc, "неизвестно"),
                icon=icon,
                who=who,
                id=entity_id,
            )
        else:
            text = self.strings("no_dc").format(icon=icon, who=who, id=entity_id)

        await utils.answer(status, text)

    @staticmethod
    async def _resolve(client, arg: str):
        """@username, username, ссылка t.me/..., числовой ID."""
        arg = arg.split()[0]
        arg = re.sub(r"^(?:https?://)?(?:t|telegram)\.me/", "", arg).strip("/")
        arg = arg.split("?")[0]
        if re.fullmatch(r"-?\d+", arg):
            arg = int(arg)
        return await client.get_entity(arg)

    @staticmethod
    def _describe(entity):
        """Возвращает (иконка, кликабельное имя)."""
        kind = type(entity).__name__
        username = getattr(entity, "username", None)

        if kind == "User":
            if getattr(entity, "deleted", False):
                return "👤", "Удалённый аккаунт"
            name = " ".join(
                p for p in (getattr(entity, "first_name", None), getattr(entity, "last_name", None)) if p
            ) or "Без имени"
            who = f'<a href="tg://user?id={entity.id}">{esc(name)}</a>'
            if username:
                who += f" (@{esc(username)})"
            icon = "🤖" if getattr(entity, "bot", False) else "👤"
            return icon, who

        title = getattr(entity, "title", None) or "Без названия"
        icon = "📢" if getattr(entity, "broadcast", False) else "👥"
        if username:
            return icon, f'<a href="https://t.me/{esc(username)}">{esc(title)}</a>'
        return icon, esc(title)

    async def _find_dc(self, client, entity):
        """DC берётся из фото профиля. Если в кэшированной сущности его нет — запрашиваем полный профиль."""
        photo = getattr(entity, "photo", None)
        if photo is not None and not getattr(photo, "personal", False):
            dc = getattr(photo, "dc_id", None)
            if dc:
                return dc

        kind = type(entity).__name__
        try:
            if kind == "User" and _USERS:
                full = await client(_USERS.GetFullUserRequest(entity))
                fu = full.full_user
                for attr in ("profile_photo", "fallback_photo"):
                    dc = getattr(getattr(fu, attr, None), "dc_id", None)
                    if dc:
                        return dc
            elif kind == "Channel" and _CHANNELS:
                full = await client(_CHANNELS.GetFullChannelRequest(entity))
                dc = getattr(getattr(full.full_chat, "chat_photo", None), "dc_id", None)
                if dc:
                    return dc
            elif kind == "Chat" and _MESSAGES:
                full = await client(_MESSAGES.GetFullChatRequest(entity.id))
                dc = getattr(getattr(full.full_chat, "chat_photo", None), "dc_id", None)
                if dc:
                    return dc
        except Exception:
            logger.debug("DCInfo: полный профиль недоступен", exc_info=True)

        return None
