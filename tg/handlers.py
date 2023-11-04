from aiogram import Dispatcher, types, Router, Bot, F
from aiogram.filters import Command
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from asgiref.sync import sync_to_async
from decouple import config

from .models import TelegramUser
from . import kb, text, chat
from .utils import get_crypto_price

bot = Bot(token=config('BOT_TOKEN'), parse_mode=ParseMode.HTML)
router = Router()


@router.message(Command("start"))
async def start_handler(msg: Message):
    user_id = msg.from_user.id
    first_name = msg.from_user.first_name
    last_name = msg.from_user.last_name
    username = msg.from_user.username

    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        username=username
    )
    if created:
        print("NEW USER ADDED")
        print(user.first_name, user.username)
    print(user.username)

    await msg.answer(text.greet.format(name=msg.from_user.full_name), reply_markup=kb.menu)


class BuyCryptoStates(StatesGroup):
    awaiting_crypto_amount = State()


class SendTextState(StatesGroup):
    awaiting_text = State()


class UserStates(StatesGroup):
    chatting_with_operator = State()


class OperatorStates(StatesGroup):
    chatting = State()
    operator_chatting = State()


a = {}


@router.callback_query()
async def handle_callback_query(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data in ["buy_ltc", "buy_btc"]:
        await handle_crypto_purchase(callback_query, state, callback_query.data[4:])
    elif callback_query.data == "confirm_purchase":
        await callback_query.message.answer(f"Отправьте на счёт YOURADMIN OPTIMA: 43255346346345"
                                            f"Время ожидания 30 МИНУТ")
    elif callback_query.data == "cancel_purchase":
        await callback_query.message.answer("Меню", reply_markup=kb.menu)
        await state.set_state(None)  # Сбросит состояние после кн-ки отмены
    elif callback_query.data == "exit":
        await callback_query.message.edit_text(text.greet.format(name=callback_query.from_user.full_name),
                                               reply_markup=kb.menu)
        await state.set_state(None)  # Сбросит состояние после кн-ки отмены
    elif callback_query.data == "operator":
        operator = 5465640772  # Оператор
        a[operator] = callback_query.from_user.id
        await state.set_state(OperatorStates.chatting)  # Установите состояние "chatting"
        await callback_query.message.answer("Вы связались с оператором. Начните писать вопросы или сообщения.")



async def handle_crypto_purchase(callback_query, state, crypto_symbol):
    crypto_price = get_crypto_price(crypto_symbol)
    crypto_price = round(crypto_price)
    await callback_query.message.answer(
        f"Текущая стоимость {crypto_symbol.upper()} составляет {crypto_price} KGS.\nВведите количество {crypto_symbol.upper()}, которое вы хотите купить:")
    await state.update_data(crypto_symbol=crypto_symbol)
    await state.set_state(BuyCryptoStates.awaiting_crypto_amount)


@router.message()
async def process_crypto_amount(msg: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == BuyCryptoStates.awaiting_crypto_amount.state:
        data = await state.get_data()
        crypto_symbol = data.get('crypto_symbol')

        try:
            crypto_amount = float(msg.text)
            crypto_price = get_crypto_price(crypto_symbol)
            total_cost = crypto_amount * crypto_price
            commission = 100
            total_cost_with_commission = round(total_cost + commission)
            await msg.answer(
                f"{crypto_amount} {crypto_symbol.upper()} будет стоить {total_cost_with_commission} KGS\n(включая комиссию в размере {commission} KGS).\nЖелаете подтвердить покупку?",
                reply_markup=kb.buy_btc if crypto_symbol == "btc" else kb.buy_ltc)
        except ValueError:
            await msg.answer("Пожалуйста, введите корректное количество криптовалюты (число).")
    else:
        await msg.answer("Извините, я не понимаю. Пожалуйста, используйте меню для навигации.")



@router.message(OperatorStates.chatting)
async def operator_chat(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    operator_id = 5465640772  # Замените этим ID вашего оператора
    if message.text == "/end_chat":
        # Если пользователь отправил команду завершения чата
        await state.set_state(OperatorStates.chatting)

        await state.clear()  # Завершаем состояние "chatting"
        del a[operator_id]
        await message.answer("Чат завершен. Вернитесь в меню.", reply_markup=kb.menu)

    else:

        await message.forward(operator_id, kwargs=message.from_user.id)


@router.message(F.from_user.id == 5465640772)
async def operator(msg: Message, state: FSMContext):
    await bot.send_message(6126380985, msg.text)


@router.message(Command("send"))
async def send_command(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    username = msg.from_user.username

    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
        user_id=user_id,
        username=username
    )
    if user.is_admin:
        await msg.answer("Введите текст, который вы хотите отправить всем пользователям.")
        await state.set_state(SendTextState.awaiting_text)
    else:
        await msg.answer("У вас нет прав для этой команды")


@router.message(SendTextState.awaiting_text)
async def handle_send_all(message: types.Message, state: FSMContext):
    text_to_send = message.text

    users = await sync_to_async(TelegramUser.objects.all)()

    for user in users:
        try:
            chat_member = await bot.get_chat_member(user.user_id, user.user_id)
            if chat_member.status != "left" and chat_member.status != "kicked":
                # Пользователь не заблокировал бота, отправляем сообщение
                await bot.send_message(user.user_id, text_to_send)
                await message.answer(f"Сообщение отправлено пользователю: {user.username}")
            else:
                await message.answer(f"Сообщение НЕ отправлено: {user.username}")
                print(f"Пользователь {user.username} заблокировал бота")
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user.username}: {str(e)}")

    await message.answer(f"Вы отправили сообщение:\n\n{text_to_send}\n\nвсем пользователям в боте.")
    await state.clear()


@router.message(Command("users"))
async def send_users(msg: Message):
    user_id = msg.from_user.id
    username = msg.from_user.username

    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
        user_id=user_id,
        username=username
    )
    if user.is_admin:
        users = await sync_to_async(TelegramUser.objects.all)()
        count = 1
        for user in users:
            await msg.answer(f"{count} {user.username}")
            count += 1
    else:
        await msg.answer("У вас нет прав!")
