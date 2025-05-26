# main.py

import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    LabeledPrice,
    PreCheckoutQuery,
    ContentType,
)
from config import TELEGRAM_TOKEN, YOOKASSA_PROVIDER_TOKEN

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher()

    # 1) /start — главное меню
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎓 Курсы",
                    web_app=WebAppInfo(url="https://velocityschool.store")
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
            "👋 Привет! Это бот школы *Velocity*.\nВыберите раздел:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    # 2) Обработка пунктов меню
    @dp.callback_query(lambda c: c.data and c.data.startswith("menu:"))
    async def menu_router(cq: types.CallbackQuery):
        action = cq.data.split(":", 1)[1]
        await cq.answer()

        if action == "contacts":
            await cq.message.answer(
                "📞 *Контакты*\n"
                "Менеджер: @YourSupportChat\n"
                "E-mail: support@velocity.ru\n"
                "Телефон: +7 123 456-78-90",
                parse_mode="Markdown"
            )

        elif action == "about":
            await cq.message.answer(
                "ℹ️ *О нас*\n"
                "Velocity — передовая онлайн-школа звука. "
                "Практикующие профи учат создавать и монетизировать музыку.",
                parse_mode="Markdown"
            )

        elif action == "links":
            links_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌐 Наш сайт", url="https://velocityschool.store")],
                [InlineKeyboardButton(text="🎥 YouTube",  url="https://youtube.com/velocity")],
                [InlineKeyboardButton(text="📱 Instagram", url="https://instagram.com/velocity")],
            ])
            await cq.message.answer(
                "🔗 *Полезные ссылки:*",
                parse_mode="Markdown",
                reply_markup=links_kb
            )

        elif action == "clear":
            await cq.message.edit_reply_markup(None)
            await cq.message.answer("🧹 Чат очищен.")

    # 3) Пришли данные из Web App → шлём ЮKassa-инвойс
    @dp.message(lambda m: m.web_app_data is not None)
    async def webapp_handler(message: types.Message):
        course_key, tariff_key = message.web_app_data.data.split(":", 1)

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

        title = titles[course_key]
        label = tariff_key.upper() if tariff_key != "single" else "Разовый"
        amount = prices_map[course_key][tariff_key]

        prices = [LabeledPrice(label=f"{title} — {label}", amount=amount * 100)]
        await bot.send_invoice(
            chat_id=message.chat.id,
            title=f"{title} — {label}",
            description="Доступ к курсу Velocity",
            provider_token=YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="buy_velocity_course",
            payload=f"{course_key}:{tariff_key}",
        )

    # 4) Подтверждаем предоплату
    @dp.pre_checkout_query()
    async def process_pre_checkout(query: PreCheckoutQuery):
        await bot.answer_pre_checkout_query(query.id, ok=True)

    # 5) Успешная оплата
    @dp.message(lambda m: m.content_type == ContentType.SUCCESSFUL_PAYMENT)
    async def successful_payment(message: types.Message):
        await message.answer("✅ Оплата получена! Скоро вышлю материалы.")

    logging.info("🚀 Velocity-бот запущен")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())