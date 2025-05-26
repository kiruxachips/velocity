# main.py

import asyncio
import logging

from yookassa import Configuration, Payment
import config

from aiogram import F, Dispatcher, types
from aiogram.client.bot import Bot, DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    ContentType,
)

from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Dispatcher
from quiz import register_quiz

logging.basicConfig(level=logging.INFO)

async def main():
    # Настройка SDK YooKassa
    Configuration.account_id = config.YOOKASSA_SHOP_ID
    Configuration.secret_key = config.YOOKASSA_SECRET_KEY

    # Инициализация бота с HTML-парсингом
    bot = Bot(
        token=config.TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Стартовое меню
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
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
        await message.answer(
            "👋 Привет! Это бот школы <b>Velocity</b>.\nВыберите раздел:",
            reply_markup=keyboard
        )

    # Обработка пунктов меню
    @dp.callback_query(lambda c: c.data and c.data.startswith("menu:"))
    async def menu_router(cq: types.CallbackQuery):
        action = cq.data.split(":", 1)[1]
        await cq.answer()
        if action == "contacts":
            await cq.message.answer(
                "📞 <b>Контакты</b>\n"
                "Telegram: @cookedbychief\n"
                "E-mail: support@velocity.ru\n"
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
                [InlineKeyboardButton(text="📚 Дзен", url="https://youtube.com/velocity")],
                [InlineKeyboardButton(text="📱 Instagram", url="https://instagram.com/velocity")],
            ])
            await cq.message.answer(
                "🔗 <b>Полезные ссылки:</b>",
                reply_markup=links_kb
            )
        else:  # clear
            await cq.message.edit_reply_markup(None)
            await cq.message.answer("🧹 Чат очищен.")

    # Приём данных из WebApp и создание платежа вручную
    @dp.message(lambda m: m.web_app_data is not None)
    async def webapp_handler(message: types.Message):
        logging.info("🕵️‍♂️ web_app_data arrived: %r", message.web_app_data.data)
        data_str = message.web_app_data.data
        logging.info(f"Получены данные из WebApp: {data_str}")

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

        if course_key not in titles or tariff_key not in prices_map[course_key]:
            return await message.answer("❌ Неизвестный курс или тариф.")

        title = titles[course_key]
        label = tariff_key.upper() if tariff_key != "single" else "Разовый"
        amount = prices_map[course_key][tariff_key]

        # Создаём платёж в YooKassa
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

        # Кнопка с ссылкой на шлюз оплаты
        pay_url = payment.confirmation.confirmation_url
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Перейти к оплате", url=pay_url)]
        ])

        await message.answer(
            f"Ваш заказ: <b>{title} — {label}</b>\n"
            f"Сумма: <b>{amount} ₽</b>\n\n"
            "Нажмите кнопку ниже, чтобы оплатить:",
            reply_markup=kb
        )
        
    register_quiz(dp)
    
    logging.info("🚀 Velocity-бот запущен")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())