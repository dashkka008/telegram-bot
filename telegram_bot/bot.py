import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F  
import asyncio
from datetime import datetime, timedelta
from geopy.distance import geodesic


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = "7906038123:AAFBoptu8WtNygQ7wZWMYXFIzEnTwWgPu9g"
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

available_workspaces = [
    {"id": i, "name": f"Место {i}", "status": "free", "booked_by": None, "booking_time": None} for i in range(1, 11)
]

def get_main_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Посмотреть доступные места")],
            [KeyboardButton(text="📅 Забронировать место"), KeyboardButton(text="📍 Чек-ин/Чек-аут")],
        ],
        resize_keyboard=True
    )
    return keyboard

def get_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить чек-ин", callback_data="checkin")],
        [InlineKeyboardButton(text="❌ Подтвердить чек-аут", callback_data="checkout")]
    ])
    return keyboard

def get_location_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)]
        ],
        resize_keyboard=True
    )
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: Message):
    markup = get_main_menu_keyboard()
    await message.reply("👋 Привет! Я бот для бронирования рабочих мест. Выберите одну из команд ниже:", reply_markup=markup)

@dp.message(F.text == "🔍 Посмотреть доступные места")
async def show_available_workspaces(message: Message):
    response = ""
    

    for ws in available_workspaces:
        status_emoji = "🟢" if ws["status"] == "free" else "🔴"
        booking_info = f" (Забронировано до {ws['booking_time']})" if ws["status"] == "booked" else ""
        response += f"{status_emoji} {ws['name']}{booking_info}\n"
    
    response += "\n🟢 — Свободно\n🔴 — Занято"
    await message.reply(response, reply_markup=get_main_menu_keyboard())

@dp.message(F.text == "📅 Забронировать место")
async def book_workspace_handler(message: Message):
    available_workspaces_list = [ws for ws in available_workspaces if ws["status"] == "free"]
    if not available_workspaces_list:
        await message.reply("⚠️ На данный момент нет доступных рабочих мест.", reply_markup=get_main_menu_keyboard())
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{ws['id']}. {ws['name']}", callback_data=f"book_{ws['id']}")] for ws in available_workspaces_list
    ])
    await message.reply("📅 Выберите свободное место для бронирования:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("book_"))
async def select_date(callback: types.CallbackQuery):
    workspace_id = int(callback.data.split("_")[1])
    dates = [
        (datetime.now() + timedelta(days=i)).strftime("%d.%m.%Y") for i in range(15)
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=date, callback_data=f"date_{workspace_id}_{(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')}")] 
        for i, date in enumerate(dates)
    ])
    await callback.message.answer(f"📅 Выберите дату для бронирования места {workspace_id} (формат: ДД.ММ.ГГГГ):", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("date_"))
async def select_time(callback: types.CallbackQuery):
    _, workspace_id, date = callback.data.split("_")
    times = [
        f"{hour:02}:00" for hour in range(9, 19)
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=time, callback_data=f"time_{workspace_id}_{date}_{time}")] for time in times
    ])
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
    await callback.message.answer(f"⏰ Выберите время для бронирования места {workspace_id} на {formatted_date}:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("time_"))
async def confirm_booking(callback: types.CallbackQuery):
    _, workspace_id, date, time = callback.data.split("_")
    workspace_id = int(workspace_id)
    start_time = f"{date} {time}:00"
    end_time = (datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S") + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

    success = update_workspace_status(workspace_id, "booked", callback.from_user.id, end_time)
    if success:
        formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
        formatted_start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")
        formatted_end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")
        await callback.message.answer(
            f"🎉 Вы успешно забронировали место {workspace_id} с {formatted_start_time} до {formatted_end_time}.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.answer("❌ Это место недоступно для бронирования.", reply_markup=get_main_menu_keyboard())
@dp.message(F.text == "📍 Чек-ин/Чек-аут")
async def check_in_out_handler(message: Message):
    await message.reply("📍 Выберите действие:", reply_markup=get_inline_keyboard()) 

@dp.callback_query(F.data == "checkin")
async def check_in(callback: types.CallbackQuery):

    await callback.message.answer("📍 Для подтверждения чек-ина отправьте свою геолокацию:", reply_markup=get_location_keyboard())

@dp.callback_query(F.data == "checkout")
async def check_out(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    for ws in available_workspaces:
        if ws["status"] == "booked" and ws["booked_by"] == user_id:
            ws["status"] = "free"
            ws["booked_by"] = None
            ws["booking_time"] = None
            await callback.message.answer("✅ Чек-аут выполнен! Место освобождено.", reply_markup=get_main_menu_keyboard())
            return
    await callback.message.answer("❌ У вас нет забронированных мест.", reply_markup=get_main_menu_keyboard())


@dp.message(F.location)
async def handle_location(message: Message):
    user_location = message.location
    office_location = (47.242352, 39.758100)
    distance = geodesic((user_location.latitude, user_location.longitude), office_location).meters

    if distance <= 100:
        await message.answer("🎉 Вы находитесь в офисе. Чек-ин выполнен!", reply_markup=get_main_menu_keyboard())
    else:
        await message.answer("❌ Вы слишком далеко от офиса.", reply_markup=get_main_menu_keyboard())

def update_workspace_status(workspace_id, new_status, user_id, booking_time):
    for ws in available_workspaces:
        if ws["id"] == workspace_id and ws["status"] == "free":
            ws["status"] = new_status
            ws["booked_by"] = user_id
            ws["booking_time"] = booking_time
            return True
    return False

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())