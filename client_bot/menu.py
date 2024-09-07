from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.callback_data import CallbackData
from databasee import *
from functions import translate_text
import os

orderdb = OrderDB()

driver_info_callback = CallbackData("driver_reg", "status", "user_id")

async def start(lang,referrer_id) -> InlineKeyboardMarkup:
    im_order = InlineKeyboardButton(text=await translate_text(text="📱 Я хочу заказать",lang=lang), callback_data=f"client_start,{referrer_id}")
    return InlineKeyboardMarkup().add(im_order)


async def registration(lang) -> InlineKeyboardMarkup:
    reg_ord = InlineKeyboardButton(text=await translate_text(text='📱 Зарегистрироватся как клиент',lang=lang), callback_data="client_start,0")
    return InlineKeyboardMarkup().add(reg_ord)


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

async def referal_inline(lang) -> InlineKeyboardMarkup:
    get_invite_link = InlineKeyboardButton(text=await translate_text(text='🔗 Получить ссылку приглашения',lang=lang), callback_data="get_invite_link")
    stat_ref = InlineKeyboardButton(text=await translate_text(text='👥 Моя Статистика',lang=lang), callback_data="stat_invite")
    return InlineKeyboardMarkup().add(get_invite_link).add(stat_ref)


async def menu_client(lang) -> ReplyKeyboardMarkup:
    profile = KeyboardButton(text=await translate_text("👤 Мой профиль",lang))
    driver_around = KeyboardButton(text=await translate_text(text='🚖 Водители рядом',lang=lang))
    make_order = KeyboardButton(text=await translate_text(text="📝 Заказать такси",lang=lang))
    referal = KeyboardButton(text=await translate_text(text="👥 Реферальная система",lang=lang))
    options = KeyboardButton(text=await translate_text("⚙️ Настройки",lang))
    return ReplyKeyboardMarkup(resize_keyboard=True).add(profile).add(driver_around,make_order).add(referal).add(options)

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

async def confirm_location(lang,latitude,longitude) -> ReplyKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=await translate_text("Подтвердить", lang), callback_data="confirm_location"),
        InlineKeyboardButton(text=await translate_text("Изменить", lang), callback_data="change_location")
    ]
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    return keyboard


async def payment_options(lang) -> InlineKeyboardMarkup:
    km_money = InlineKeyboardButton(text=await translate_text(text='💰 Сменить цену на 1км',lang=lang), callback_data="changekmmoney")
    bonus = InlineKeyboardButton(text=await translate_text(text='🎁 Сменить процент бонуса от денег',lang=lang), callback_data="changebonus")
    return InlineKeyboardMarkup().add(km_money).add(bonus)


async def options(lang) -> InlineKeyboardMarkup:
    photo = InlineKeyboardButton(text=await translate_text(text='🤳 Сменить фотографию аккаунта',lang=lang), callback_data="changephoto")
    name = InlineKeyboardButton(text=await translate_text(text='📋 Сменить имя аккаунта',lang=lang), callback_data="changename")
    change_lang = InlineKeyboardButton(text=await translate_text(text='💬 Сменить язык',lang=lang), callback_data="changelang")
    send_bonus = InlineKeyboardButton(text=await translate_text('🎁 Отправить бонус пользователю',lang), callback_data="send_bonus")
    stat_voditelem = InlineKeyboardButton(text=await translate_text(text='🚖 Стать водителем',lang=lang), url=f'{os.getenv("URL_FOR_DRIVER_BOT")}')
    return InlineKeyboardMarkup().add(photo).add(name).add(change_lang).add(send_bonus).add(stat_voditelem)

async def moder_pick(user_id,lang):
    accept = InlineKeyboardButton(text=await translate_text('✅ Подтвердить',lang), callback_data=driver_info_callback.new(status=1,user_id = user_id))
    decline = InlineKeyboardButton(text=await translate_text('🚫 Отклонить',lang), callback_data=driver_info_callback.new(status=0, user_id = user_id))
    return InlineKeyboardMarkup().add(accept, decline)

async def cancel_menu(lang):
    cancel = InlineKeyboardButton(text=await translate_text('❌ Отменить',lang), callback_data="CancelL")
    return InlineKeyboardMarkup().add(cancel)

async def menu_driver(lang) -> ReplyKeyboardMarkup:
    profile = KeyboardButton(text=await translate_text("👤 Мой профиль",lang))
    driver_around = KeyboardButton(text=await translate_text(text='🚖 Водители рядом',lang=lang))
    make_order = KeyboardButton(text=await translate_text("📝 Заказать такси",lang))
    referal = KeyboardButton(text=await translate_text("👥 Реферальная система",lang))
    options = KeyboardButton(text=await translate_text("⚙️ Настройки",lang))
    return ReplyKeyboardMarkup(resize_keyboard=True).add(profile).add(driver_around,make_order).add(referal).add(options)

async def phone_share(lang) -> ReplyKeyboardMarkup:
    phone = KeyboardButton(text=await translate_text("☎️ Поделится номером", lang), request_contact=True)
    return ReplyKeyboardMarkup(resize_keyboard=True).add(phone)

async def location(lang) -> ReplyKeyboardMarkup:
    location = KeyboardButton(text=await translate_text("📍 Отправить текущее местоположение",lang),request_location=True)
    return ReplyKeyboardMarkup(resize_keyboard=True).add(location)

async def confirm_keyboard(lang,bonus,money) -> InlineKeyboardMarkup:
    paymoney = InlineKeyboardButton(text=await translate_text(f"💰 Оплатить деньгами из баланса {money}",lang),callback_data=f"paymoney,{money}")
    paybonus = InlineKeyboardButton(text=await translate_text(f"🎁 Оплатить бонусами {bonus}",lang),callback_data=f"paybonus,{bonus}")
    cancel = InlineKeyboardButton(text=await translate_text("❌ Отменить",lang),callback_data="cancel_pay")
    return InlineKeyboardMarkup().add(paymoney).add(paybonus).add(cancel)

async def poisk_type(lang) -> InlineKeyboardMarkup:
    search = InlineKeyboardButton(text = await translate_text("🔎 По адресу",lang),callback_data="search_adres")
    geo = InlineKeyboardButton(text = await translate_text("📍 По геопозиции",lang),callback_data="search_geo")
    cancel = InlineKeyboardButton(text=await translate_text('❌ Отменить',lang), callback_data="CancelL")
    return InlineKeyboardMarkup().add(search,geo).add(cancel)

async def messages(lang) -> InlineKeyboardMarkup:
    check_hist = InlineKeyboardButton(text=await translate_text("🛎️ Посмотреть сообщения",lang),callback_data="messages")
    return InlineKeyboardMarkup().add(check_hist)

async def generate_order_menu(order_id,lang):
    join_button = InlineKeyboardButton(await translate_text("✅ Присоединиться",lang), callback_data=f"join,{order_id}")
    decline_button = InlineKeyboardButton(await translate_text("❌ Отклонить",lang), callback_data=f"decline")
    keyboard = InlineKeyboardMarkup().add(join_button,decline_button)
    return keyboard

async def confirm_order(order, lang) -> InlineKeyboardMarkup:
    accept = InlineKeyboardButton(text=await translate_text('🆗 Принять заказ',lang), callback_data=f"confirmorder,{order}")
    return InlineKeyboardMarkup().add(accept)

async def accept_temp_order(lang,nearpoints) -> InlineKeyboardMarkup:
    accept = InlineKeyboardButton(text=await translate_text('🆗 Принять заказ',lang), callback_data=f"confirmtempord,{nearpoints}")
    decline = InlineKeyboardButton(text=await translate_text('❌ Отклонить',lang), callback_data=f"declinetempord")
    return InlineKeyboardMarkup().add(accept).add(decline)

async def driver_here(client_id, lang, driver_id) -> InlineKeyboardMarkup:
    accept = InlineKeyboardButton(text=await translate_text('Я приехал',lang), callback_data=f"driverhere,{client_id},{driver_id}")
    return InlineKeyboardMarkup().add(accept)

async def complete_order(order, lang) -> InlineKeyboardMarkup:
    accept = InlineKeyboardButton(text=await translate_text('🆗 Подтвердить заказ',lang), callback_data=f"complete_order,{order}")
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