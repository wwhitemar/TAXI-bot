from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.callback_data import CallbackData
from databasee import *
from functions import translate_text
import os

orderdb = OrderDB()
clientdb = ClientDB()
driverdb = DriverDB()
taxiorderdb = Order_Taxi_DB()

driver_info_callback = CallbackData("driver_reg", "status", "user_id")

async def start(lang) -> InlineKeyboardMarkup:
    im_driver = InlineKeyboardButton(text=await translate_text('🚗 Я водитель',lang), callback_data="driver_start")
    return InlineKeyboardMarkup().add(im_driver)


async def registration(lang) -> InlineKeyboardMarkup:
    reg_drive = InlineKeyboardButton(text=await translate_text('🚗 Зарегистрироватся как водитель',lang), callback_data="driver_start")
    return InlineKeyboardMarkup().add(reg_drive)


language_inlinekeyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [
            KeyboardButton(text="Русский"),
            KeyboardButton(text="English"),
            KeyboardButton(text="Lietuvių"),
            KeyboardButton(text="Polski")
        ]
    ]
)

async def choose_gender(lang) -> ReplyKeyboardMarkup:
    male = KeyboardButton(text=await translate_text("Мужской",lang))
    female = KeyboardButton(text=await translate_text("Женский",lang))
    return ReplyKeyboardMarkup(resize_keyboard=True).add(male,female)

async def choose_category_driver(lang) -> ReplyKeyboardMarkup:
    ip = KeyboardButton(text=await translate_text("Индивидуальный предприниматель",lang))
    se = KeyboardButton(text=await translate_text("Самозанятый",lang))
    return ReplyKeyboardMarkup(resize_keyboard=True).add(ip,se)

async def confirm_location(lang,latitude,longitude) -> ReplyKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=await translate_text("Подтвердить", lang), callback_data="confirm_location"),
        InlineKeyboardButton(text=await translate_text("Изменить", lang), callback_data="change_location")
    ]
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    return keyboard



async def menu_admin(lang) -> ReplyKeyboardMarkup:
    ban_user = KeyboardButton(text=await translate_text(text='🚫 Забанить пользователя',lang=lang))
    unban_user = KeyboardButton(text=await translate_text(text="✅ Разбанить пользователя",lang=lang))
    make_moderator = KeyboardButton(text=await translate_text(text="🚧 Выдать модератора",lang=lang))
    unmake_moderator = KeyboardButton(text=await translate_text(text="🔨 Снять модератора",lang=lang))
    payment_opt = KeyboardButton(text=await translate_text(text="🎫 Нстройки платежа",lang=lang))
    give_bonus = KeyboardButton(text=await translate_text(text="🎁 Выдавать бонусы",lang=lang))
    ungive_bonus = KeyboardButton(text=await translate_text(text="🗡🎁 Снять бонусы",lang=lang))
    get_bd = KeyboardButton(text=await translate_text(text="📝 Получить базу данных",lang=lang))
    exit = KeyboardButton(text=await translate_text(text="❌ Выйти из меню",lang=lang))
    return ReplyKeyboardMarkup(resize_keyboard=True).add(ban_user,unban_user).add(make_moderator,unmake_moderator).add(payment_opt).add(give_bonus,ungive_bonus).add(get_bd).add(exit)

async def payment_options(lang) -> InlineKeyboardMarkup:
    km_money = InlineKeyboardButton(text=await translate_text(text='💰 Сменить цену на 1км',lang=lang), callback_data="changekmmoney")
    bonus = InlineKeyboardButton(text=await translate_text(text='🎁 Сменить процент бонуса от денег',lang=lang), callback_data="changebonus")
    return InlineKeyboardMarkup().add(km_money).add(bonus)

async def menu_driver(lang) -> ReplyKeyboardMarkup:
    profile = KeyboardButton(text=await translate_text("👤 Мой профиль",lang))
    tekushi_zakaz = KeyboardButton(text=await translate_text("📝 Текущий заказ",lang))
    create_zakaz = KeyboardButton(text=await translate_text("✏ Создать заказ",lang))
    update_location = KeyboardButton(text=await translate_text("📍 Обновить текущее местоположение",lang))
    options = KeyboardButton(text=await translate_text("⚙️ Настройки",lang))
    return ReplyKeyboardMarkup(resize_keyboard=True).add(profile).add(tekushi_zakaz,create_zakaz).add(update_location).add(options)

async def options(lang, id) -> InlineKeyboardMarkup:
    photo = InlineKeyboardButton(text=await translate_text(text='🤳 Сменить фотографию аккаунта',lang=lang), callback_data="changephoto")
    name = InlineKeyboardButton(text=await translate_text(text='📋 Сменить имя аккаунта',lang=lang), callback_data="changename")
    change_lang = InlineKeyboardButton(text=await translate_text(text='💬 Сменить язык',lang=lang), callback_data="changelang")  
    change_active = InlineKeyboardButton(text=await translate_text(f'''{'✅ Вы в сети' if driverdb.get_driver(id)[8] == 'active' else '❌ Вы не в сети'}''',lang), callback_data=f"{f'changeactive,{id}' if driverdb.get_driver(id)[8] == 'offline' else f'changeoffline,{id}'}")
    stat_clientom = InlineKeyboardButton(text=await translate_text('👤 Стать заказчиком',lang), url=f'{os.getenv("URL_FOR_CLIENT_BOT")}')
    return InlineKeyboardMarkup().add(photo).add(name).add(change_lang).add(change_active).add(stat_clientom)

async def moder_pick(user_id,lang):
    accept = InlineKeyboardButton(text=await translate_text('✅ Подтвердить',lang), callback_data=driver_info_callback.new(status=1,user_id = user_id))
    decline = InlineKeyboardButton(text=await translate_text('🚫 Отклонить',lang), callback_data=driver_info_callback.new(status=0, user_id = user_id))
    return InlineKeyboardMarkup().add(accept, decline)

async def cancel_menu(lang):
    cancel = InlineKeyboardButton(text=await translate_text('❌ Отменить',lang), callback_data="CancelL")
    return InlineKeyboardMarkup().add(cancel)

async def menu_client(lang) -> ReplyKeyboardMarkup:
    profile = KeyboardButton(text=await translate_text("👤 Мой профиль",lang))
    tekushi_zakaz = KeyboardButton(text=await translate_text("📝 Текущий заказ",lang))
    create_zakaz = KeyboardButton(text=await translate_text("✏ Создать заказ",lang))
    update_location = KeyboardButton(text=await translate_text("📍 Обновить текущее местоположение",lang))
    options = KeyboardButton(text=await translate_text("⚙️ Настройки",lang))
    return ReplyKeyboardMarkup(resize_keyboard=True).add(profile).add(tekushi_zakaz,create_zakaz).add(update_location).add(options)

async def generate_order_menu(order_id,lang):
    join_button = InlineKeyboardButton(await translate_text("Показать",lang), callback_data=f"viewtaxiord,{order_id}")
    keyboard = InlineKeyboardMarkup().add(join_button)
    return keyboard


async def phone_share(lang) -> ReplyKeyboardMarkup:
    phone = KeyboardButton(text=await translate_text("☎️ Поделится номером", lang), request_contact=True)
    return ReplyKeyboardMarkup(resize_keyboard=True).add(phone)

async def location(lang) -> ReplyKeyboardMarkup:
    location = KeyboardButton(text=await translate_text("📍 Отправить текущее местоположение",lang),request_location=True)
    return ReplyKeyboardMarkup(resize_keyboard=True).add(location)

async def confirm_keyboard(lang) -> ReplyKeyboardMarkup:
    yes = KeyboardButton(text=await translate_text("Да",lang))
    no = KeyboardButton(text=await translate_text("Нет",lang))
    return ReplyKeyboardMarkup(resize_keyboard=True).add(yes,no)

async def poisk_type(lang) -> InlineKeyboardMarkup:
    search = InlineKeyboardButton(text = await translate_text("🔎 По адресу",lang),callback_data="search_adres")
    geo = InlineKeyboardButton(text = await translate_text("📍 По геопозиции",lang),callback_data="search_geo")
    cancel = InlineKeyboardButton(text=await translate_text('❌ Отменить',lang), callback_data="CancelL")
    return InlineKeyboardMarkup().add(search,geo).add(cancel)

async def get_client_locations(clients_ids):
    clients_ids = [str(clients_ids).replace('[','').replace(']','')]
    for id_client in clients_ids:
        name = clientdb.get_client_name(id_client)[0]
        client = InlineKeyboardButton(text = f"{name}",callback_data=f"ordfromtaxi,{id_client}")
        return InlineKeyboardMarkup().add(client)

async def messages(lang) -> InlineKeyboardMarkup:
    check_hist = InlineKeyboardButton(text=await translate_text("🛎️ Посмотреть сообщения",lang),callback_data="messages")
    return InlineKeyboardMarkup().add(check_hist)

async def confirm_order(order, lang) -> InlineKeyboardMarkup:
    accept = InlineKeyboardButton(text=await translate_text('🆗 Принять заказ',lang), callback_data=f"confirmorder,{order}")
    return InlineKeyboardMarkup().add(accept)

async def driver_here(client_id, lang, driver_id) -> InlineKeyboardMarkup:
    accept = InlineKeyboardButton(text=await translate_text('Я приехал',lang), callback_data=f"driverhere,{client_id},{driver_id}")
    return InlineKeyboardMarkup().add(accept)

async def complete_order(order, lang) -> InlineKeyboardMarkup:
    accept = InlineKeyboardButton(text=await translate_text('🆗 Завершить заказ',lang), callback_data=f"complete_order,{order}")
    return InlineKeyboardMarkup().add(accept)

test_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [
            KeyboardButton(text="a)"),
            KeyboardButton(text="b)"),
        ],
        [
            KeyboardButton(text="c)")
        ]
    ]
)