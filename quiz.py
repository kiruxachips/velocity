# quiz.py
"""
Модуль опросника для Telegram-бота Velocity.
Содержит состояния FSM и регистрацию хендлеров для квиза "Какой курс подойдёт тебе?".
"""
from collections import Counter

from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter


class QuizStates(StatesGroup):
    branch = State()  # звук или визуал
    q2     = State()  # вопрос 2
    q3     = State()  # вопрос 3
    q4     = State()  # вопрос 4


def register_quiz(dp: Dispatcher) -> None:
    """
    Регистрирует хендлеры для квиза в диспетчере dp.
    """

    @dp.callback_query(lambda c: c.data == 'quiz_start')
    async def quiz_start(cq: types.CallbackQuery, state: FSMContext):
        await cq.answer()
        # Инициализация хранения ответов
        await state.update_data(answers={})
        await state.set_state(QuizStates.branch)
        # Первый вопрос
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔊 Управлять звуком", callback_data="sound")],
            [InlineKeyboardButton(text="🎨 Управлять визуалом", callback_data="visual")],
        ])
        await cq.message.answer(
            "📍 Ты стоишь на старте. Тебе дают суперсилу. Какую выберешь?",
            reply_markup=kb
        )

    @dp.callback_query(StateFilter(QuizStates.branch))
    async def branch_chosen(cq: types.CallbackQuery, state: FSMContext):
        await cq.answer()
        choice = cq.data  # 'sound' или 'visual'
        data = await state.get_data()
        data['answers']['branch'] = choice
        await state.update_data(data)

        # Следующий вопрос в зависимости от ветки
        if choice == 'sound':
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎵 Делать музыку с нуля", callback_data="beatmaking")],
                [InlineKeyboardButton(text="⚙️ Сводить и обрабатывать звук", callback_data="sound_engineering")],
                [InlineKeyboardButton(text="🔊 Создавать эффекты для игр/фильмов", callback_data="sound_design")],
            ])
            text = "🔉 Что из этого тебе ближе?"
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📃 Постеры и бренд-визуал", callback_data="graphic")],
                [InlineKeyboardButton(text="🖥 3D-модели и анимация", callback_data="three_d")],
                [InlineKeyboardButton(text="🏛 Архитектурная визуализация", callback_data="architecture")],
            ])
            text = "🧩 Какие образы вызывают у тебя больше интереса?"

        await cq.message.answer(text, reply_markup=kb)
        await state.set_state(QuizStates.q2)

    @dp.callback_query(StateFilter(QuizStates.q2))
    async def q2_handler(cq: types.CallbackQuery, state: FSMContext):
        await cq.answer()
        choice = cq.data
        data = await state.get_data()
        data['answers']['q2'] = choice
        await state.update_data(data)

        branch = data['answers']['branch']
        if branch == 'sound':
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💡 Придумывать и сочинять", callback_data="creative")],
                [InlineKeyboardButton(text="🔧 Настраивать и доводить до идеала", callback_data="technical")],
                [InlineKeyboardButton(text="🚀 Исследовать и удивлять", callback_data="experimental")],
            ])
            text = "🎛 Какой тип задач тебе интереснее?"
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎨 Комбинировать цвета и шрифты", callback_data="graphic")],
                [InlineKeyboardButton(text="📸 Вращать камеру и настраивать свет", callback_data="three_d")],
                [InlineKeyboardButton(text="🗺 Проектировать логично и красиво", callback_data="architecture")],
            ])
            text = "🛠 Что тебе ближе?"

        await cq.message.answer(text, reply_markup=kb)
        await state.set_state(QuizStates.q3)

    @dp.callback_query(StateFilter(QuizStates.q3))
    async def q3_handler(cq: types.CallbackQuery, state: FSMContext):
        await cq.answer()
        choice = cq.data
        data = await state.get_data()
        data['answers']['q3'] = choice
        await state.update_data(data)

        branch = data['answers']['branch']
        if branch == 'sound':
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🪩 Немного писал музыку / крутил биты", callback_data="tried_music")],
                [InlineKeyboardButton(text="🎚 Знаком со сведением — хочу глубже", callback_data="tried_engineering")],
                [InlineKeyboardButton(text="❓ Никогда не пробовал, но хочется", callback_data="never_tried")],
            ])
            text = "🎧 Что ты уже пробовал?"
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🖌 Photoshop / Canva / Figma", callback_data="graphic")],
                [InlineKeyboardButton(text="🔄 Игрался с 3D-редакторами", callback_data="three_d")],
                [InlineKeyboardButton(text="📐 Никогда не пробовал, но тянет в архитектуру", callback_data="architecture")],
            ])
            text = "📚 С чем ты уже сталкивался?"

        await cq.message.answer(text, reply_markup=kb)
        await state.set_state(QuizStates.q4)

    @dp.callback_query(StateFilter(QuizStates.q4))
    async def q4_handler(cq: types.CallbackQuery, state: FSMContext):
        await cq.answer()
        choice = cq.data
        data = await state.get_data()
        data['answers']['q4'] = choice
        answers = data['answers']

        # Подсчёт рекомендаций
        if answers['branch'] == 'sound':
            votes = [
                answers['q2'],
                'beatmaking' if answers['q3']=='creative'
                else 'sound_engineering' if answers['q3']=='technical'
                else 'sound_design',
                'beatmaking' if answers['q4']=='tried_music'
                else 'sound_engineering' if answers['q4']=='tried_engineering'
                else 'sound_design',
            ]
            course_map = {
                'beatmaking': '🎓 Битмейкинг',
                'sound_engineering': '🎓 Звукорежиссура',
                'sound_design': '🎓 Саунд-дизайн'
            }
        else:
            votes = [answers['q2'], answers['q3'], answers['q4']]
            course_map = {
                'graphic': '🎓 Графический дизайн',
                'three_d': '🎓 3D-моделирование',
                'architecture': '🎓 Архитектурное проектирование'
            }

        most_common = Counter(votes).most_common(1)[0][0]
        recommendation = course_map.get(most_common, '🎓 Наш курс')

        await cq.message.answer(
            f"🔥 Готов узнать больше?\nТебе подходит курс:\n👉 {recommendation}"
        )
        await state.clear()