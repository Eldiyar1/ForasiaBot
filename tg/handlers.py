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


def get_ltc_price():
    url = "https://openexchangerates.org/api/latest.json?app_id=84c6243309e84299a2b028f8c55d21d8"
    response = requests.get(url)
    data = response.json()

    usd_to_kgs = data['rates']['KGS']

    url = "https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()
    ltc_to_usd = data['litecoin']['usd']

    ltc_to_kgs = ltc_to_usd * usd_to_kgs

    return ltc_to_kgs


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


class BuyLtcStates(StatesGroup):
    awaiting_ltc_amount = State()


@router.callback_query()
async def handle_callback_query(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "buy_ltc":
        ltc_price = get_ltc_price()
        await callback_query.message.answer(f"Текущая стоимость LTC составляет {ltc_price} KGS. Введите количество LTC, которое вы хотите купить:")
        await state.set_state(BuyLtcStates.awaiting_ltc_amount)
    elif callback_query.data == "confirm_purchase_ltc":
        await callback_query.message.answer(f"Отправьте на счёт YOURADMIN OPTIMA: 43255346346345"
                                            f"Время ожидания 30 МИНУТ")
    elif callback_query.data == "cancel_purchase":
        await callback_query.message.answer("Меню", reply_markup=kb.menu)


@router.message(BuyLtcStates.awaiting_ltc_amount)
async def handle_ltc_amount(message: types.Message, state: FSMContext):
    ltc_amount = message.text
    cost = float(ltc_amount) * get_ltc_price() + 100  # Рассчет стоимости с учетом актуального курса и комиссии
    await message.answer(f"Покупка {ltc_amount} LTC будет стоить {cost} кыргызских сомов.", reply_markup=kb.buy_ltc)
    await state.clear()