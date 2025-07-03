# main.py

import asyncio
import logging

from yookassa import Configuration, Payment
import config

from aiogram import types
from aiogram.client.bot import Bot
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Dispatcher
from aiogram.client.default import DefaultBotProperties

from quiz import register_quiz

logging.basicConfig(level=logging.INFO)

# 1) Reply-клавиатура с кнопкой "Меню"
menu_reply_kb = ReplyKeyboardMarkup(
    keyboard=[
        [ KeyboardButton(text="Меню") ]
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)

# 2) Фабрика Inline-клавиатуры
def get_main_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📚 Подбор курса", callback_data="quiz_start"),
            InlineKeyboardButton(
                text="🎓 Курсы",
                web_app=WebAppInfo(url="https://velocityschool.store/")
            ),
            InlineKeyboardButton(text="📞 Контакты", callback_data="menu:contacts"),
        ],
        [
            InlineKeyboardButton(text="ℹ️ О нас", callback_data="menu:about"),
            InlineKeyboardButton(text="🔗 Полезные", callback_data="menu:links"),
        ],
        [
            InlineKeyboardButton(text="🗑 Очистить чат", callback_data="menu:clear"),
        ],
    ])

async def main():
    # 3) Настройка YooKassa SDK
    Configuration.account_id = config.YOOKASSA_SHOP_ID
    Configuration.secret_key = config.YOOKASSA_SECRET_KEY

    # 4) Инициализация бота
    if config.TELEGRAM_TOKEN is None:
        raise ValueError("TELEGRAM_TOKEN не задан в config.py")
    bot = Bot(
        token=config.TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher(storage=MemoryStorage())

    # 5) /start — показывает inline-меню и Reply-кнопку "Меню"
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        await message.answer(
            "👋 Привет! Это бот школы <b>Velocity</b>.\nВыберите раздел:",
            reply_markup=get_main_inline_kb()
        )
        await message.answer(
            "👉 В любой момент нажмите «Меню» внизу, чтобы открыть это меню снова.",
            reply_markup=menu_reply_kb
        )

    # 6) Кнопка Reply-клавиатуры "Меню"
    @dp.message(lambda m: m.text == "Меню")
    async def on_menu_button(message: types.Message):
        # просто переиспользуем логику /start
        await cmd_start(message)

    # 7) Обработка пунктов inline-меню
    @dp.callback_query(lambda c: c.data and c.data.startswith("menu:"))
    async def menu_router(cq: types.CallbackQuery):
        await cq.answer()
        if not cq.data:
            return
        action = cq.data.split(":", 1)[1]

        if not cq.message:
            return

        if action == "contacts":
            await cq.message.answer(
                "📞 <b>Контакты</b>\n"
                "Telegram: @cookedbychief\n"
                "E-mail: support@velocityschool.ru\n"
                "Телефон: +7 963 299-87-02"
            )
        elif action == "about":
            await cq.message.answer(
                "ℹ️ <b>О нас</b>\n"
                "Velocity — передовая онлайн-школа звука. "
                "Практикующие профи учат создавать и монетизировать музыку."
            )
        elif action == "links":
            links_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌐 Наш сайт", url="https://velocityschool.ru/")],
                [InlineKeyboardButton(text="📚 Дзен", url="https://dzen.ru/velocity")],
                [InlineKeyboardButton(text="📱 Instagram", url="https://instagram.com/velocity")],
            ])
            await cq.message.answer(
                "🔗 <b>Полезные ссылки:</b>",
                reply_markup=links_kb
            )
        else:  # clear
            # убираем inline-кнопки и сообщаем об очистке
            await cq.message.answer("🧹 Чат очищен.")

    # 8) Обработка WebApp-данных и создание платежа
    @dp.message(lambda m: m.web_app_data is not None)
    async def webapp_handler(message: types.Message):
        data_str = getattr(getattr(message, "web_app_data", None), "data", None)
        logging.info("🕵️‍♂️ web_app_data arrived: %r", data_str)
        if not data_str:
            return await message.answer("❌ Некорректные данные от WebApp.")

        try:
            course_key, tariff_key = data_str.split(":", 1)
        except ValueError:
            return await message.answer("❌ Некорректные данные от WebApp.")

        titles = {
            "sound_engineer": "Звукорежиссёр с нуля",
            "beatmaker":      "Битмейкер с нуля",
            "sound_designer": "Саунд-дизайнер с нуля",
        }
        prices_map = {
            "sound_engineer": {"pro": 37500, "intro": 24000, "single": 2500},
            "beatmaker":      {"pro": 30000, "intro": 16000, "single": 2500},
            "sound_designer": {"pro": 40000, "intro": 28000, "single": 2500},
        }

        if course_key not in titles or tariff_key not in prices_map.get(course_key, {}):
            return await message.answer("❌ Неизвестный курс или тариф.")

        title = titles[course_key]
        label = tariff_key.upper() if tariff_key != "single" else "Разовый"
        amount = prices_map[course_key][tariff_key]

        payment = Payment.create({
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://velocityschool.store/return"
            },
            "capture": True,
            "description": f"{title} — {label}"
        })

        pay_url = None
        if payment and hasattr(payment, "confirmation") and payment.confirmation:
            pay_url = getattr(payment.confirmation, "confirmation_url", None)
        if not pay_url:
            return await message.answer("❌ Не удалось создать ссылку на оплату. Попробуйте позже.")
        pay_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Перейти к оплате", url=pay_url)]
        ])

        await message.answer(
            f"Ваш заказ: <b>{title} — {label}</b>\n"
            f"Сумма: <b>{amount} ₽</b>\n\n"
            "Нажмите кнопку ниже, чтобы оплатить:",
            reply_markup=pay_kb
        )

    # 9) Регистрируем викторину из quiz.py
    register_quiz(dp)

    logging.info("🚀 Velocity-бот запущен")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())