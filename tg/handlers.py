from aiogram import Dispatcher, types, Router
from aiogram.filters import Command

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from asgiref.sync import sync_to_async
import requests
from .models import TelegramUser
from . import kb, text

router = Router()


def get_crypto_price(crypto_symbol):
    url = "https://openexchangerates.org/api/latest.json?app_id=84c6243309e84299a2b028f8c55d21d8"
    response = requests.get(url)
    data = response.json()

    usd_to_kgs = data['rates']['KGS']

    if crypto_symbol == "ltc":
        crypto_key = "litecoin"
    elif crypto_symbol == "btc":
        crypto_key = "bitcoin"
    else:
        raise ValueError("Invalid cryptocurrency symbol")

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_key}&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()

    crypto_to_usd = data[crypto_key]['usd']
    crypto_to_kgs = crypto_to_usd * usd_to_kgs

    return crypto_to_kgs


class BuyLtcStates(StatesGroup):
    awaiting_ltc_amount = State()


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


@router.callback_query()
async def handle_callback_query(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data in ["buy_ltc", "buy_btc"]:
        await handle_crypto_purchase(callback_query, state, callback_query.data[4:])
    elif callback_query.data == "confirm_purchase":
        await callback_query.message.answer(f"Отправьте на счёт YOURADMIN OPTIMA: 43255346346345"
                                            f"Время ожидания 30 МИНУТ")
    elif callback_query.data == "cancel_purchase":
        await callback_query.message.answer("Меню", reply_markup=kb.menu)


async def handle_crypto_purchase(callback_query, state, crypto_symbol):
    crypto_price = get_crypto_price(crypto_symbol)
    await callback_query.message.answer(
        f"Текущая стоимость {crypto_symbol.upper()} составляет {crypto_price} KGS. Введите количество {crypto_symbol.upper()}, которое вы хотите купить:")
    await state.update_data(crypto_symbol=crypto_symbol)
    await state.set_state(BuyCryptoStates.awaiting_crypto_amount)


@router.message()
async def process_crypto_amount(msg: Message, state: FSMContext):
    data = await state.get_data()
    crypto_symbol = data['crypto_symbol']

    try:
        crypto_amount = float(msg.text)
        crypto_price = get_crypto_price(crypto_symbol)
        total_cost = crypto_amount * crypto_price
        await msg.answer(
            f"{crypto_amount} {crypto_symbol.upper()} будет стоить {total_cost} KGS. Желаете подтвердить покупку?",
            reply_markup=kb.buy_btc if crypto_symbol == "btc" else kb.buy_ltc)
    except ValueError:
        await msg.answer("Пожалуйста, введите корректное количество криптовалюты (число).")
