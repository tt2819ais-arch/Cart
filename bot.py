import re
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest

TOKEN = "8491774226:AAHvZR02IZ4lhUAmgFCuCOAYE9atAmbcYKc"

ADMINS = {
    "MaksimXyila",
    "ar_got",
}

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ====== STATE ======
state = {
    "drop": None,
    "rub_limit": 0,
    "current_turnover": 0,
    "operations": 0,
    "last_input": 0,
    "waiting_email": False,
    "pinned_form_msg_id": None,
}

EMAIL_REGEX = re.compile(r"sir\+\d+@outluk\.ru", re.IGNORECASE)
SUM_REGEX = re.compile(r"!?(\d+)!?")
INPUT_REGEX = re.compile(
    r"(вход|пришло|капнуло|прилетело)\s*(\d+)",
    re.IGNORECASE
)


def is_admin(message: Message) -> bool:
    return message.from_user and message.from_user.username in ADMINS


def is_group(message: Message) -> bool:
    return message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP)


@dp.message()
async def main_handler(message: Message):
    if not is_group(message):
        return

    username = message.from_user.username if message.from_user else None
    text = message.text or ""

    # ===== IGNORE NON ADMINS (EXCEPT DROP IN STRICT CASES) =====
    if not is_admin(message):
        # allow drop only to send анкета and email
        if state["drop"] and username == state["drop"]:
            if state["waiting_email"] and EMAIL_REGEX.fullmatch(text):
                state["waiting_email"] = False
                await message.answer(
                    f"• Вход: {state['last_input']}₽\n"
                    f"• Текущий оборот: {state['current_turnover']}₽\n"
                    f"• Количество операций: {state['operations']}\n"
                    f"• Установленный оборот: {state['rub_limit']}₽"
                )
        return

    # ===== SET DROP =====
    if text.lower().startswith("дроп @"):
        drop_username = text.split("@", 1)[1].strip()
        state.update({
            "drop": drop_username,
            "current_turnover": 0,
            "operations": 0,
            "last_input": 0,
            "waiting_email": False
        })

        msg = await message.answer(
            "Привет, давай заполним небольшую анкету чтобы начать работу😁\n"
            "(Надо будет отметить дропа!!)\n"
            "ФИО:\n"
            "номер карты:\n"
            "номер счета:\n"
            "номер телефона:\n"
            "Пожалуйста, отправьте данные одним сообщением."
        )

        try:
            await bot.pin_chat_message(message.chat.id, msg.message_id)
            state["pinned_form_msg_id"] = msg.message_id
        except TelegramBadRequest:
            pass
        return

    # ===== CONNECTING PHRASES =====
    if text.lower() in ("подключаю", "щас подключу"):
        if not state["drop"]:
            return

        await message.answer(
            f"@{state['drop']}\n\n"
            "Сейчас тебе будет приходить денюжка. Каждое поступление — мне скрин из истории операций. "
            "Не отдельного перевода, а прям страницу истории, списком.\n"
            "Следи за этим, мне надо сразу сообщать (скидывать скрин), как прилетит денюжка.\n\n"
            "Как накопится необходимая сумма — отправлю реквизиты и сумму (конкретная сумма!). "
            "Надо будет перевести, только внимательно (!!!).\n\n"
            "После перевода отправляешь квитанцию на указанную почту."
        )
        return

    # ===== SET TURNOVER LIMIT =====
    if text.startswith("/rub"):
        try:
            state["rub_limit"] = int(text.split()[1])
        except Exception:
            return
        return

    # ===== INPUT MONEY =====
    m = INPUT_REGEX.search(text)
    if m:
        amount = int(m.group(2))
        state["last_input"] = amount
        state["current_turnover"] += amount
        state["operations"] += 1

        await message.answer(
            f"• Вход: {amount}₽\n"
            f"• Текущий оборот: {state['current_turnover']}₽\n"
            f"• Количество операций: {state['operations']}\n"
            f"• Установленный оборот: {state['rub_limit']}₽"
        )
        return

    # ===== TRANSFER SUM DETECTION =====
    if SUM_REGEX.fullmatch(text.strip()):
        state["waiting_email"] = True
        return


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
