# -*- coding: utf-8 -*-
import asyncio
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import Throttled
from aiogram.types import CallbackQuery
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.utils.exceptions import BotBlocked
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher import filters
from aiogram.types import ChatType
from aiogram.types import InputFile
from aiogram.types import ReplyKeyboardRemove
from states import *
from yandex_geocoder import Client
import menu
from dotenv import load_dotenv
import os
from functions import *
from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from is_filter import *
from databasee import *
import config

# env
load_dotenv()

# Настройки бота
YANDEX_GEOCODER_API_KEY = config.YANDEX_GEOCODER_API_KEY
admin_id = int(config.ADMIN_ID)

# Инициализация бота и диспетчера
taxi_bot = Bot(token=config.API_TOKEN_TAXI,parse_mode='HTML')
client_bot = Bot(config.API_TOKEN_CLIENT, parse_mode='HTML') 
dp = Dispatcher(taxi_bot, storage=MemoryStorage())

# Инициализация клиента геокодера Яндекс
geocoder = Client(YANDEX_GEOCODER_API_KEY)


# Инициализация базы данных
clientdb = ClientDB()
driverdb = DriverDB()
orderdb = OrderDB()
langdb = LangDB()
moderatordb = ModeratorDB()
zayavki_driverdb = Zayavki_driverDB()
temprefdb = Temp_refDB()
taxiorderdb = Order_Taxi_DB()
tempordersdb = Temp_OrdersTable()

dp.filters_factory.bind(IsDriver)

# защита от спама
class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit=0.5, key_prefix="antiflood_"):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(ThrottlingMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()
        if handler:
            limit = getattr(handler, "throttling_rate_limit", self.rate_limit)
            key = getattr(handler, "throttling_key", f"{self.prefix}_{handler.__name__}")
        else:
            limit = self.rate_limit
            key = f"{self.prefix}_message"
        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            await self.message_throttled(message, t)
            raise CancelHandler()

    async def message_throttled(self, message: types.Message, throttled: Throttled):
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()
        if handler:
            key = getattr(handler, "throttling_key", f"{self.prefix}_{handler.__name__}")
        else:
            key = f"{self.prefix}_message"
        delta = throttled.rate - throttled.delta
        if throttled.exceeded_count <= 2:
            await message.reply("<b>❗ Don't spam.</b>")
        await asyncio.sleep(delta)
        thr = await dispatcher.check_key(key)

def rate_limit(limit: int, key=None):
    def decorator(func):
        setattr(func, "throttling_rate_limit", limit)
        if key:
            setattr(func, "throttling_key", key)
        return func
    return decorator

# Обработчик команды /start
@dp.message_handler(commands="start", state="*")
@rate_limit(2, 'start')
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    check_driver = driverdb.check_driver_in_db(message.from_user.id)
    start_text = '''Добро пожаловать в социальное   сообщество Freestyle Future (далее FF) 

Цель сообщества сократить  выбросы CO² и снизить загруженность дорог, применяя свободные места автомобилей, движущихся по умолчанию, далее ( *полезная поездка*)
Водитель, согласившийся взять попутчика, производит бартер и в знак благодарности 
получает компенсацию в виде горючего, запчастей и всего прочьего кроме денег. Это исключает спекулятивный характер и стабилизирует ценообразования в бюджетном сегменте.  
Каждый кто использует ПП,  является соучастником проекта Гринпис,  в котором будут рассажены деревья (в статистиком соотношении)
Объем компенсации определяется  статистикой *Полезных Поездок*, для учёта которых используются бонусы.  Бенефициары бонусов могут ими делится для поездок третьих лиц  и получать компенсации в выше указанном формате, возвращая их в систему.  Эта одна из формул, определяющая рискоориентированность относительно существования сообщества.  Каждый из членов сообщества может является водителем и пассажиром, если это не противоречит социальным нормам и законам, применяемые в данный период времени.  
Родиной этого проекта является *Литва*, и ни какие страны не имеют к этому отношение, но это не исключает вероятность применения в других странах.  
Данный проект является *авторским*, а  аналогии могут являться случайным подобием или плагиатом. 
Наш следующий этап создать более логически интегрированное приложение.  Будем благодарны за любую помощь в развитии сообщества. 
PS: Причиной позднего ответа от тех поддержки в форме обратной связи может быть кадровый кризис,  который определяется самой структурой сообщества


<b>Нажатием на кнопку ниже вы соглашаетесь с данным соглашением.</b>'''
    if check_driver:
        lang = langdb.get_lang(message.from_user.id)
        await message.answer(await translate_text(f"Добро пожаловать {message.from_user.full_name}\n Ваш айди : {message.from_user.id}", lang),reply_markup= await menu.start(lang))
    else:
        await message.answer(await translate_text(start_text, 'en'),reply_markup= await menu.start('en'))

    # Добавляем кнопку "Старт" слева от поля ввода сообщения
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('/start'))
    await message.answer("Нажмите кнопку /start для начала работы", reply_markup=keyboard)

# Обработчик кнопок выбора языка
@dp.message_handler(content_types=['text'],text=["Lietuvių", "English", "Русский", "Polski"],state=Chose_lang.lang)
async def set_language(message: types.Message):
    chosen_language = message.text
    if chosen_language == "Lietuvių":
        chosen_language = "lt"
    elif chosen_language == "English":
        chosen_language = "en"
    elif chosen_language == "Русский":
        chosen_language = "ru"
    elif chosen_language == "Polski":
        chosen_language = "pl"
    # Сохраняем выбранный язык пользователя в базе данных
    langdb.add_lang(message.from_user.id,chosen_language)
    # Отправляем сообщение с подтверждением выбора языка
    await message.answer(await translate_text(f"Язык установлен на {message.text}", chosen_language))
    await message.answer(await translate_text("Напишите ваше Фамилия Имя Отчество", chosen_language))
    await Client_Start.name.set()

@dp.callback_query_handler(text_startswith="client_start", state=None) 
async def client_start(q: types.CallbackQuery):
    check_client = clientdb.check_client_in_db(q.from_user.id)
    if check_client:
        lang = langdb.get_lang(q.from_user.id)
        await q.message.answer(await translate_text("Вы уже зарегистрированы.", lang), reply_markup=await menu.menu_client(lang))
    else:
        referrer_id = q.data.split(',')[1]
        temprefdb.add_temp_ref(q.from_user.id,referrer_id)
        try:
            lang = langdb.get_lang(q.from_user.id)
        except:
            lang = False
        if lang:
            await q.message.answer(await translate_text("Напишите ваше Фамилия Имя Отчество",lang))
            await Client_Start.name.set()
        else:
            await q.message.answer("Choose your language:", reply_markup=menu.language_inlinekeyboard)
            await Chose_lang.lang.set()

@dp.message_handler(state=Client_Start.name)
async def client_start(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    lang = langdb.get_lang(message.from_user.id)
    await message.answer(await translate_text("Пожалуйста поделитесь своим номером.", lang),reply_markup= await menu.phone_share(lang))
    await Client_Start.phone.set()

@dp.message_handler(content_types=[types.ContentType.CONTACT],state=Client_Start.phone)
async def phone_client(message: types.Message, state: FSMContext):
    lang = langdb.get_lang(message.from_user.id)
    contact = message.contact
    phone_number = contact.phone_number
    await state.update_data(phone=phone_number)
    await message.answer(await translate_text("Пожалуйста отправьте место отправки", lang),reply_markup= await menu.location(lang))
    await Client_Start.latitude_longitude.set()

@dp.message_handler(content_types=[types.ContentType.LOCATION],state=Client_Start.latitude_longitude)
async def client_start(message: types.Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude
    latitude_longitude = [latitude,longitude]
    await state.update_data(latitude_longitude=latitude_longitude)
    data = await state.get_data()
    name = data.get('name')
    lat_long = data.get('latitude_longitude')
    phone = data.get('phone')
    try:
        referal_id = temprefdb.get_temp_ref(message.from_user.id)
    except:
        referal_id = 0
    location = await get_address(latitude,longitude)
    clientdb.add_client(message.from_user.id,name,phone,latitude,longitude,f"{location}",referal_id)
    lang = langdb.get_lang(message.from_user.id)
    await message.answer(await translate_text("✅ Вы успешно зарегистрировались!\n\n🤳 Пришлите фотографию аккаунта.", lang),reply_markup= await menu.menu_client(lang))
    temprefdb.delete_temp_ref(message.from_user.id)
    try:
        lang_referal = langdb.get_lang(referal_id)
    except:
        pass
    try:
        await taxi_bot.send_message(referal_id,await translate_text(f"<b>👥 У вас новый реферальный пользователь!</b>\n\nТеперь у вас <i>{clientdb.get_referral_count(referal_id)}</i> реферальных пользователей!",lang_referal))
    except:
        pass
    await state.finish()
    await Profile_photo.photo.set()

@dp.message_handler(content_types=[types.ContentType.PHOTO], state=Profile_photo.photo)
async def handle_docs_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    # Сохраняем фото
    photo = message.photo[-1]
    photo_id = photo.file_id
    file = await taxi_bot.get_file(photo_id)
    file_path = file.file_path
    destination = f'avatars/{user_id}.jpg'
    await taxi_bot.download_file(file_path, destination)
    lang = langdb.get_lang(user_id)
    try:
        # Обновляем аватар пользователя
        clientdb.update_avatar(user_id,destination)
    except:
        pass
    try:
        driverdb.update_avatar(user_id,destination)
    except:
        pass

    await message.reply(await translate_text("Фотография успешно обновлен!",lang))
    
    await state.finish()

@dp.message_handler(content_types=['text'], text=['👥 Реферальная система', translate_text_sync('👥 Реферальная система', 'en'), translate_text_sync('👥 Реферальная система', 'pl'), translate_text_sync('👥 Реферальная система', 'lt')])
async def referal_system(message: types.Message):
    ban_client = clientdb.get_ifbanned_client(message.from_user.id)
    lang = langdb.get_lang(message.from_user.id)
    if ban_client == 0:
        await message.answer(await translate_text("👥 Меню реферальной системы",lang),reply_markup= await menu.referal_inline(lang))
    else:
        await message.answer(await translate_text("🔒 Вы забанены",lang))

@dp.message_handler(content_types=['text'], text=['👤 Мой профиль', translate_text_sync('👤 Мой профиль', 'en'), translate_text_sync('👤 Мой профиль', 'pl'), translate_text_sync('👤 Мой профиль', 'lt')])
async def profile(message: types.Message):
    user_id = message.from_user.id
    try:
        user = clientdb.check_client_in_db(user_id)
    except:
        user = False
    try:
        driver = driverdb.check_driver_in_db(user_id)
    except:
        driver = False
    try:
        ban_client = clientdb.get_ifbanned_client(user_id)
    except:
        ban_client = 1
    try:
        ban_driver = driverdb.get_ifbanned_driver(user_id)
    except:
        ban_driver = 1
    lang = langdb.get_lang(user_id)
    photo = InputFile(f'avatars/{user_id}.jpg')
    if ban_client == 0 and ban_driver == 0 and user and driver:
        await message.answer_photo(photo=photo,caption=await translate_text(f'''<b>👤 Мой профиль</b> <i>[Пользователь]</i>
ID : {user_id}
ФИО : {clientdb.get_client(user_id)[2]}
Бонусы : {clientdb.get_client(user_id)[2]}

<b>👤 Мой профиль</b> <i>[Водитель]</i>
ID : {user_id}
ФИО : {driverdb.get_driver(user_id)[2]}
''',lang))
    elif ban_client == 0 and user:
        await message.answer_photo(photo=photo,caption=await translate_text(f'''<b>👤 Мой профиль</b> <i>[Пользователь]</i>
ID : {user_id}
ФИО : {clientdb.get_client(user_id)[2]}
Бонусы : {clientdb.get_client(user_id)[2]}''',lang))
    elif ban_driver == 0 and driver:
        await message.answer_photo(photo=photo,caption=await translate_text(f'''<b>👤 Мой профиль</b> <i>[Водитель]</i>
ID : {user_id}
ФИО : {driverdb.get_driver(user_id)[2]}''',lang))
    else:
        await message.answer(await translate_text("🔒 Вы забанены", lang))


@dp.callback_query_handler(text="changephoto")
async def changephoto(q = types.CallbackQuery):
    lang = langdb.get_lang(q.from_user.id)
    await taxi_bot.send_message(q.from_user.id,await translate_text("Отправьте фотографию",lang))
    await Profile_photo.photo.set()

@dp.message_handler(content_types=['text'], state=Change_name.name)
async def handle_change_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = langdb.get_lang(user_id)
    name = message.text
    try:
        # Обновляем аватар пользователя
        clientdb.update_client_name(user_id,name)
        await message.reply(await translate_text("Имя успешно обновлен!",lang))
    except:
        pass
    try:
        driverdb.update_driver_name(user_id, name)
    except:
        pass

    await state.finish()


@dp.callback_query_handler(text="changename")
async def changephoto(q = types.CallbackQuery):
    lang = langdb.get_lang(q.from_user.id)
    await taxi_bot.send_message(q.from_user.id,await translate_text("Введите ваше Фамилия Имя Отчество",lang),reply_markup= await menu.cancel_menu(lang))
    await Change_name.name.set()

@dp.message_handler(content_types=['text'],text=["Lietuvių", "English", "Русский", "Polski"],state=Change_lang.lang)
async def set_language(message: types.Message, state: FSMContext):
    chosen_language = message.text
    if chosen_language == "Lietuvių":
        chosen_language = "lt"
    elif chosen_language == "English":
        chosen_language = "en"
    elif chosen_language == "Русский":
        chosen_language = "ru"
    elif chosen_language == "Polski":
        chosen_language = "pl"
    # Сохраняем выбранный язык пользователя в базе данных
    langdb.set_lang(message.from_user.id,chosen_language)
    # Отправляем сообщение с подтверждением выбора языка
    await message.answer(await translate_text(f"Язык установлен на {message.text}", chosen_language),reply_markup= await menu.menu_client(chosen_language))
    await state.finish()

@dp.callback_query_handler(text="changelang")
async def changephoto(q = types.CallbackQuery):
    lang = langdb.get_lang(q.from_user.id)
    await taxi_bot.send_message(q.from_user.id,await translate_text("Выберите язык",lang),reply_markup=menu.language_inlinekeyboard)
    await Change_lang.lang.set()


@dp.message_handler(content_types=['text'], text=['⚙️ Настройки', translate_text_sync('⚙️ Настройки', 'en'), translate_text_sync('⚙️ Настройки', 'pl'), translate_text_sync('⚙️ Настройки', 'lt')])
async def options(message: types.Message):
    user_id = message.from_user.id
    try:
        user = clientdb.check_client_in_db(user_id)
    except:
        user = False
    try:
        driver = driverdb.check_driver_in_db(user_id)
    except:
        driver = False
    try:
        ban_client = clientdb.get_ifbanned_client(user_id)
    except:
        ban_client = 1
    try:
        ban_driver = driverdb.get_ifbanned_driver(user_id)
    except:
        ban_driver = 1
    lang = langdb.get_lang(user_id)
    if ban_client == 0 and ban_driver == 0 and user and driver:
        await message.answer(await translate_text(f'''⚙️ Настройки''',lang),reply_markup= await menu.options(lang,message.from_user.id))
    elif ban_client == 0 and user:
        await message.answer(await translate_text(f'''⚙️ Настройки''',lang),reply_markup= await menu.options(lang,message.from_user.id))
    elif ban_driver == 0 and driver:
        await message.answer(await translate_text(f'''⚙️ Настройки''',lang),reply_markup= await menu.options(lang,message.from_user.id))
    else:
        await message.answer(await translate_text("🔒 Вы забанены", lang))

@dp.callback_query_handler(text="get_invite_link")
async def get_invite_link(q: types.CallbackQuery):
    taxi_bot_info = await taxi_bot.get_me()
    user_id = q.from_user.id
    lang = langdb.get_lang(user_id)
    await q.message.reply(await translate_text("🔗 <b>Пригласите своих друзей, используя эту ссылку</b>",lang) + f"\n\n<code>https://t.me/{taxi_bot_info.username}?start={user_id}</code>")

@dp.callback_query_handler(text="stat_invite")
async def show_stats(q: types.CallbackQuery):
    user_id = q.from_user.id
    referral_count = clientdb.get_referral_count(user_id)
    lang = langdb.get_lang(user_id)
    if referral_count >= 5:
        await q.message.reply(await translate_text(f"👥 У вас {referral_count} рефералов.",lang))
    elif referral_count == 1:
        await q.message.reply(await translate_text(f"👥 У вас {referral_count} реферал.",lang))
    else:
        await q.message.reply(await translate_text(f"👥 У вас {referral_count} реферала.",lang))

@dp.callback_query_handler(text_startswith="changeactive")
async def change_active(q: types.CallbackQuery):
    ids = q.data.split(',')[1]
    driverdb.update_driver_status(ids,'active')
    lang = langdb.get_lang(ids)
    await q.message.edit_reply_markup(reply_markup=await menu.options(lang,ids))

@dp.callback_query_handler(text_startswith="changeoffline")
async def change_active(q: types.CallbackQuery):
    ids = q.data.split(',')[1]
    driverdb.update_driver_status(ids,'offline')
    lang = langdb.get_lang(ids)
    await q.message.edit_reply_markup(reply_markup=await menu.options(lang,ids))


@dp.message_handler(content_types=['text'],text=["Lietuvių", "English", "Русский", "Polski"],state=Driver_Start.lang)
async def set_language(message: types.Message):
    chosen_language = message.text
    if chosen_language == "Lietuvių":
        chosen_language = "lt"
    elif chosen_language == "English":
        chosen_language = "en"
    elif chosen_language == "Русский":
        chosen_language = "ru"
    elif chosen_language == "Polski":
        chosen_language = "pl"
    # Сохраняем выбранный язык пользователя в базе данных
    langdb.add_lang(message.from_user.id,chosen_language)
    # Отправляем сообщение с подтверждением выбора языка
    await message.answer(await translate_text(f"Язык установлен на {message.text}", chosen_language))
    await message.answer(await translate_text('Выберите категорию водителя\n\n<i>/start чтобы начать сначала</i>',chosen_language),reply_markup= await menu.choose_category_driver(chosen_language))
    await Driver_Start.category.set()


# Обработчик для регистрации водителя
@dp.callback_query_handler(text="driver_start")
async def start_driver_registration(q: types.CallbackQuery, state: FSMContext):
    await state.finish()
    check_driver = driverdb.check_driver_in_db(q.from_user.id)
    if check_driver:
        lang = langdb.get_lang(q.from_user.id)
        await taxi_bot.send_message(chat_id=q.from_user.id,text=await translate_text("Вы уже зарегистрированы как водитель.", lang), reply_markup=await menu.menu_driver(lang))
    else:
        try:
            lang = langdb.get_lang(q.from_user.id)
            await q.message.answer(await translate_text('Выберите категорию водителя\n\n<i>/start чтобы начать сначала</i>',lang),reply_markup= await menu.choose_category_driver(lang))
            await Driver_Start.category.set()
        except:
            await q.message.answer("Choose your language:", reply_markup=menu.language_inlinekeyboard)
            await Driver_Start.lang.set()

@dp.message_handler(content_types=['text'],state=Driver_Start.category)
async def save_driver_name(message: types.Message, state: FSMContext):
    lang = langdb.get_lang(message.from_user.id)
    if await translate_text(message.text,'ru') == 'Индивидуальный предприниматель':
        await state.update_data(category='A')
        cl = clientdb.get_client(message.from_user.id)
        if cl is not None:
            await message.answer(await translate_text('Напишите ваше Фамилия Имя Отчество\n\n<i>/start чтобы начать сначала</i>',lang),reply_markup= ReplyKeyboardRemove())
            await Driver_Start.name.set()
        else:
            await message.answer(await translate_text('<b>❗Внимание❗</b>\n<b>Регистрация отменена</b>\n<b>Чтобы стать водителем нужно иметь профиль заказчика!</b>\n\n/start Чтобы начать сначала',lang),parse_mode='html', reply_markup=ReplyKeyboardRemove())
            await state.finish()
    elif await translate_text(message.text,'ru') == 'Самозанятый':
        await state.update_data(category='B')
        cl = clientdb.get_client(message.from_user.id)
        if cl is not None:
            await message.answer(await translate_text('Напишите ваше Фамилия Имя Отчество\n\n<i>/start чтобы начать сначала</i>',lang),reply_markup= ReplyKeyboardRemove())
            await Driver_Start.name.set()
        else:
            await message.answer(await translate_text('<b>❗Внимание❗</b>\n<b>Регистрация отменена</b>\n<b>Чтобы стать водителем нужно иметь профиль заказчика!</b>\n\n/start Чтобы начать сначала',lang),parse_mode='html', reply_markup=ReplyKeyboardRemove())
            await state.finish()
    else:
        await message.answer('Выберите из предложенных вариантов')
        await Driver_Start.category.set()


# Обработчик для сохранения имени водителя
@dp.message_handler(state=Driver_Start.name)
async def save_driver_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    lang = langdb.get_lang(message.from_user.id)
    await message.answer(await translate_text("Теперь укажите марку, модель и цвет вашей машины.\n\n<i>/start чтобы начать сначала</i>",lang), reply_markup=ReplyKeyboardRemove())
    await Driver_Start.car.set()

# Обработчик для сохранения марки и модели машины
@dp.message_handler(state=Driver_Start.car)
async def save_driver_car(message: types.Message, state: FSMContext):
    await state.update_data(car=message.text)
    lang = langdb.get_lang(message.from_user.id)
    await message.answer(await translate_text("Хорошо! Теперь укажите номер вашей машины.\n\n<i>/start чтобы начать сначала</i>", lang))
    await Driver_Start.car_number.set()

# Обработчик для сохранения номера машины
@dp.message_handler(state=Driver_Start.car_number)
async def save_driver_car_number(message: types.Message, state: FSMContext):
    await state.update_data(car_number=message.text)
    lang = langdb.get_lang(message.from_user.id)

    await message.answer(await translate_text("Отлично! Теперь отправьте ваше текущее местоположение.\n\n<i>[💡 Подсказка] Нажмите на скрепку,потом на геоданные,и на картах отмечайте место откуда будете ехать\n<b>Если хотите быстрое определение текущего местоположения, можете нажать на кнопку который появился у вас внизу ввода текста.</b></i>\n\n\n<i>/start чтобы начать заново</i>",lang),reply_markup= await menu.location(lang))
    await Driver_Start.latitude_longitude.set()

# Обработчик для сохранения геолокации водителя
@dp.message_handler(content_types=[types.ContentType.LOCATION], state=Driver_Start.latitude_longitude)
async def save_driver_location(message: types.Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude
    lang = langdb.get_lang(message.from_user.id)
    await state.update_data(latitude=latitude, longitude=longitude)
    await message.answer(await translate_text("Теперь отправьте ваш номер телефона.\n\n<i>/start чтобы начать сначала</i>",lang),reply_markup= await menu.phone_share(lang))
    await Driver_Start.phone.set()
    

@dp.message_handler(content_types=[types.ContentType.CONTACT],state=Driver_Start.phone)
async def save_driver_phone(message: types.Message, state: FSMContext):
    lang = langdb.get_lang(message.from_user.id)
    contact = message.contact
    phone_number = contact.phone_number
    await state.update_data(phone=phone_number)
    await message.answer(await translate_text('Отправьте ваше водительское удостоверение в виде фотографии.\n\n<i>/start чтобы начать сначала</i>',lang),reply_markup= ReplyKeyboardRemove())
    await Driver_Start.voditel_prava.set()

@dp.message_handler(content_types=[types.ContentType.PHOTO],state=Driver_Start.voditel_prava)
async def handle_docs_voditel_prava(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    # Сохраняем фото
    photo = message.photo[-1]
    photo_id = photo.file_id
    file = await taxi_bot.get_file(photo_id)
    file_path = file.file_path
    destination = f'driver_license_photos/{user_id}.jpg'
    await taxi_bot.download_file(file_path, destination)
    # Получение данных о водителе из состояния FSM
    data = await state.get_data()
    name = data.get('name')
    car = data.get('car')
    car_number = data.get('car_number')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    phone = data.get('phone')
    category = data.get('category')

    location = await get_address(latitude,longitude)
    # Завершение состояния FSM
    await state.finish()
    # Сохранение данных в базе данных
    lang = langdb.get_lang(message.from_user.id)
    username = message.from_user.username
    zayavki_driverdb.add_zayavka(message.from_user.id,name,car,car_number,latitude,longitude,location,phone,category,username)
    await message.answer(await translate_text("<b>❄️ Ваша заявка на проверке.</b>\n\nБот скажет когда тебя примут!", lang),reply_markup=ReplyKeyboardRemove())
    
    moderators = moderatordb.get_moderators()
    if moderators:
        for moderator in moderators:
            lang_moder = langdb.get_lang(moderator[0])
            photo = InputFile(f'driver_license_photos/{user_id}.jpg')
            await taxi_bot.send_photo(moderator[0],photo,caption=await translate_text(f"<b>Поступила заявка на регистрацию водителя от @{message.from_user.username}\n</b>"
                                        f"\nID: <b>{message.from_user.id}</b>\n\n"
                                        f"ФИО. <b>{name}</b>\n"
                                        f"Машина. <b>{car}</b>\n"
                                        f"Номер машины. <b>{car_number}</b>\n"
                                        f"Номер телефона. <i>{phone}</i>\n"
                                        f"Категория. <b>{category}</b>",lang_moder),reply_markup= await menu.moder_pick(message.from_user.id,lang_moder))
    lang_admin = langdb.get_lang(admin_id)
    photo = InputFile(f'driver_license_photos/{user_id}.jpg')
    await taxi_bot.send_photo(admin_id,photo,caption=await translate_text(f"<b>Поступила заявка на регистрацию водителя от @{message.from_user.username}\n</b>"
                                    f"\nID: <b>{message.from_user.id}</b>\n\n"
                                    f"ФИО. <b>{name}</b>\n"
                                    f"Машина. <b>{car}</b>\n"
                                    f"Номер машины. <b>{car_number}</b>\n"
                                    f"Номер телефона. <i>{phone}</i>\n"
                                    f"Категория. <b>{category}</b>",lang_admin),reply_markup= await menu.moder_pick(message.from_user.id,lang_admin))


@dp.callback_query_handler(menu.driver_info_callback.filter(status='1'))
async def accept_form(call: CallbackQuery, callback_data: dict):
    try:
        driver = zayavki_driverdb.get_zayavka(callback_data.get("user_id"))
        driverdb.add_driver(driver[0],driver[1],driver[2],driver[3],driver[4],driver[5],driver[6],driver[7],driver[8],driver[9])
        await taxi_bot.edit_message_caption(caption=f'''{call.message.caption}\n\n✅''', chat_id=call.message.chat.id,message_id=call.message.message_id)
        lang_driver = langdb.get_lang(callback_data.get("user_id"))
        await taxi_bot.send_message(callback_data.get("user_id"), '🥳', reply_markup=await menu.menu_driver(lang_driver))
        await taxi_bot.send_message(callback_data.get("user_id"), await translate_text(f'<b>✅ Ваша заявка на водителя одобрена модераторами</b>\n\nОбновите фотографию профиля в меню настройках чтобы начать пользоватся ботом!',lang_driver), parse_mode='HTML')
        driver = zayavki_driverdb.get_zayavka(callback_data.get("user_id"))
        zayavki_driverdb.delete_zayavka(callback_data.get("user_id"))
        callback_data.clear()
    except:
        lang = langdb.get_lang(call.from_user.id)
        await call.message.delete()
        await call.message.answer(await translate_text("Ошибка: Заявка уже была принята или отклонена!",lang))


@dp.callback_query_handler(menu.driver_info_callback.filter(status='0'))
async def accept_form(call: CallbackQuery, callback_data: dict):
    try:
        zayavki_driverdb.delete_zayavka(callback_data.get("user_id"))
        await taxi_bot.edit_message_caption(caption=f"{call.message.caption}\n\n🚫", chat_id=call.message.chat.id,message_id=call.message.message_id)
        lang_driver = langdb.get_lang(callback_data.get("user_id"))
        await taxi_bot.send_message(callback_data.get("user_id"), await translate_text("<b>🛑 Ваша заявка была отклонена.</b>",lang_driver), parse_mode='HTML')
        callback_data.clear()
    except:
        lang = langdb.get_lang(call.from_user.id)
        await call.message.delete()
        await call.message.answer(await translate_text("Ошибка: Заявка уже была принята или отклонена!",lang))


@dp.message_handler(commands="admin", state="*")
async def handle_admin(message: types.Message):
    lang = langdb.get_lang(message.from_user.id)
    if message.from_user.id == admin_id:
        await message.answer(await translate_text("Клавиатура обновлена.",lang),reply_markup= await menu.menu_admin(lang))
    else:
        pass

@dp.message_handler(content_types=['text'], text=['🚫 Забанить пользователя', translate_text_sync('🚫 Забанить пользователя', 'en'), translate_text_sync('🚫 Забанить пользователя', 'lt'), translate_text_sync('🚫 Забанить пользователя', 'pl')])
async def ban_user(message: types.Message):
    lang = langdb.get_lang(message.from_user.id)
    if message.from_user.id == admin_id:
        await message.answer(await translate_text("Напишите телеграм айди пользователя",lang),reply_markup= await menu.cancel_menu(lang))
        await Banusr.user.set()
    else:
        pass

@dp.message_handler(content_types=['text'], state=Banusr.user)
async def ban_user(message: types.Message, state: FSMContext):
    lang = langdb.get_lang(message.from_user.id)
    id = message.text
    try:
        lang_client = langdb.get_lang(id)
        clientdb.ban_client(id)
        await message.answer(await translate_text("🔒 Аккаунт пользователя забанен",lang))
        await client_bot.send_message(id,await translate_text("🔒 Ваш аккаунт пользователя забенен\nВы не можете пользоватся функционалом заказчика.",lang_client))
    except:
        await message.answer(await translate_text("❌ Аккаунт пользователя не существует",lang))
    try:
        driverdb.ban_driver(id)
        lang_driver = langdb.get_lang(id)
        await message.answer(await translate_text("🔒 Аккаунт водителя забанен",lang))
        await taxi_bot.send_message(id,await translate_text("🔒 Ваш аккаунт водителя забанен\nВы не можете пользоватся функционалом водителя.",lang_driver))
    except:
        await message.answer(await translate_text("❌ Аккаунт водителя не существует",lang))
    await state.finish()

@dp.message_handler(content_types=['text'], text=['✅ Разбанить пользователя', translate_text_sync('✅ Разбанить пользователя', 'en'), translate_text_sync('✅ Разбанить пользователя', 'lt'), translate_text_sync('✅ Разбанить пользователя', 'pl')])
async def unban_user(message: types.Message):
    lang = langdb.get_lang(message.from_user.id)
    if message.from_user.id == admin_id:
        await message.answer(await translate_text("Напишите телеграм айди пользователя",lang),reply_markup= await menu.cancel_menu(lang))
        await Unbanusr.user.set()
    else:
        pass

@dp.message_handler(content_types=['text'], state=Unbanusr.user)
async def unban_user(message: types.Message, state: FSMContext):
    lang = langdb.get_lang(message.from_user.id)
    id = message.text
    try:
        lang_client = langdb.get_lang(id)
        clientdb.unban_client(id)
        await message.answer(await translate_text("🔓 Аккаунт пользователя разбанен",lang))
        await client_bot.send_message(id,await translate_text("🔓 Ваш аккаунт пользователя разбанен\nВы можете пользоватся функционалом заказчика.",lang_client))
    except:
        await message.answer(await translate_text("❌ Аккаунт пользователя не существует",lang))
    try:
        driverdb.unban_driver(id)
        lang_driver = langdb.get_lang(id)
        await message.answer(await translate_text("🔓 Аккаунт водителя разбанен",lang))
        await taxi_bot.send_message(id,await translate_text("🔓 Ваш аккаунт водителя разбанен\nВы можете пользоватся функционалом водителя.",lang_driver))
    except:
        await message.answer(await translate_text("❌ Аккаунт водителя не существует",lang))
    await state.finish()

@dp.message_handler(content_types=['text'], text=['🚧 Выдать модератора', translate_text_sync('🚧 Выдать модератора', 'en'), translate_text_sync('🚧 Выдать модератора', 'lt'), translate_text_sync('🚧 Выдать модератора', 'pl')])
async def unban_user(message: types.Message):
    lang = langdb.get_lang(message.from_user.id)
    if message.from_user.id == admin_id:
        await message.answer(await translate_text("Напишите телеграм айди пользователя",lang),reply_markup= await menu.cancel_menu(lang))
        await Addmoder.user.set()
    else:
        pass

@dp.message_handler(content_types=['text'], state=Addmoder.user)
async def unban_user(message: types.Message, state: FSMContext):
    lang = langdb.get_lang(message.from_user.id)
    id = message.text
    try:
        lang_moder = langdb.get_lang(id)
        moderatordb.add_moderator(id)
        await message.answer(await translate_text("🚧 Модератор успешно добавлен",lang_moder))
        try:
            await taxi_bot.send_message(id,await translate_text("🚧 Вам выдали права модератора.",lang_moder))
        except:
            pass
        try:
            await client_bot.send_message(id,await translate_text("🚧 Вам выдали права модератора.",lang_moder))
        except:
            pass
    except:
        await message.answer(await translate_text("❌ Аккаунт пользователя не существует",lang))
    await state.finish()

@dp.message_handler(content_types=['text'], text=['🔨 Снять модератора', translate_text_sync('🔨 Снять модератора', 'en'), translate_text_sync('🔨 Снять модератора', 'lt'), translate_text_sync('🔨 Снять модератора', 'pl')])
async def unban_user(message: types.Message):
    lang = langdb.get_lang(message.from_user.id)
    if message.from_user.id == admin_id:
        await message.answer(await translate_text("Напишите телеграм айди пользователя",lang))
        await Deletemoder.user.set()
    else:
        pass

@dp.message_handler(content_types=['text'], state=Deletemoder.user)
async def unban_user(message: types.Message, state: FSMContext):
    lang = langdb.get_lang(message.from_user.id)
    id = message.text
    try:
        lang_moder = langdb.get_lang(id)
        moderatordb.delete_moderator(id)
        await message.answer(await translate_text("🚧 Модератор успешно удален",lang_moder))
        try:
            await taxi_bot.send_message(id,await translate_text("🚧 Вас сняли с поста модератора.",lang_moder))
        except:
            await client_bot.send_message(id,await translate_text("🚧 Вас сняли с поста модератора.",lang_moder))
    except:
        await message.answer(await translate_text("❌ Аккаунт пользователя не существует",lang))
    await state.finish()
@dp.message_handler(content_types=['text'], text=['🎫 Нстройки платежа', translate_text_sync('🎫 Нстройки платежа', 'en'), translate_text_sync('🎫 Нстройки платежа', 'lt'), translate_text_sync('🎫 Нстройки платежа', 'pl')])
async def payments_options(message: types.Message):
    lang = langdb.get_lang(message.from_user.id)
    if message.from_user.id == admin_id:
        await message.answer(await translate_text("Настройки платежа",lang),reply_markup= await menu.payment_options(lang))
    else:
        pass

@dp.callback_query_handler(text='changekmmoney')
async def change_km_money(call: types.CallbackQuery):
    lang = langdb.get_lang(call.from_user.id)
    await call.message.answer(await translate_text("Введите цену за 1 километр",lang),reply_markup= await menu.cancel_menu(lang))
    await ChangePaymentsOptions.km.set()

@dp.message_handler(content_types=['text'], state=ChangePaymentsOptions.km)
async def changekm(message: types.Message, state: FSMContext):
    lang = langdb.get_lang(message.from_user.id)
    km = message.text
    try:
        config = read_config()
        config['Pricing']['cost_per_km'] = km
        write_config(config)
        await message.answer(await translate_text(f"✅ Успешно обновлен цена за 1 км на {km} руб.",lang))
        await state.finish()
    except:
        await message.answer(await translate_text("Ошибка в системе.\n\nСнимите данный Exception чтобы смотреть ошибку.",lang))
        await state.finish()

@dp.callback_query_handler(text='changebonus')
async def change_km_money(call: types.CallbackQuery):
    lang = langdb.get_lang(call.from_user.id)
    await call.message.answer(await translate_text("Введите процент который будет взятся для бонуса",lang),reply_markup= await menu.cancel_menu(lang))
    await ChangePaymentsOptions.precent_bonus.set()

@dp.message_handler(content_types=['text'], state=ChangePaymentsOptions.precent_bonus)
async def changekm(message: types.Message, state: FSMContext):
    lang = langdb.get_lang(message.from_user.id)
    km = message.text
    try:
        config = read_config()
        config['Pricing']['max_bonus_percentage'] = km
        write_config(config)
        await message.answer(await translate_text(f"✅ Успешно обновлен процент на {km}",lang))
        await state.finish()
    except:
        await message.answer(await translate_text("Ошибка в системе.",lang))
        await state.finish()

        
@dp.message_handler(content_types=['text'], text=['📝 Получить базу данных', translate_text_sync('📝 Получить базу данных', 'en'), translate_text_sync('📝 Получить базу данных', 'lt'), translate_text_sync('📝 Получить базу данных', 'pl')])
async def unban_user(message: types.Message):
    with open("database/data.db", "rb") as doc:
        await taxi_bot.send_document(admin_id, doc, caption=f"<b>DATABASE</b>")

@dp.message_handler(content_types=['text'], text=['❌ Выйти из меню',  translate_text_sync('❌ Выйти из меню', 'en'),  translate_text_sync('❌ Выйти из меню', 'lt'),  translate_text_sync('❌ Выйти из меню', 'pl')])
async def payments_options(message: types.Message):
    lang = langdb.get_lang(message.from_user.id)
    if message.from_user.id == admin_id:
        await message.answer("✅",reply_markup= await menu.menu_client(lang))
    else:
        pass

@dp.callback_query_handler(text='CancelL',state='*')
async def cancel_all(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    lang = langdb.get_lang(call.from_user.id)
    await call.message.answer(await translate_text("❌ Операция отменена",lang))
    await state.finish()

@dp.message_handler(content_types=['text'], text=['🎁 Выдавать бонусы', translate_text_sync('🎁 Выдавать бонусы', 'en'), translate_text_sync('🎁 Выдавать бонусы', 'lt'), translate_text_sync('🎁 Выдавать бонусы', 'pl')])
async def payments_options(message: types.Message):
    lang = langdb.get_lang(message.from_user.id)
    if message.from_user.id == admin_id:
        await message.answer(await translate_text("Напишите ID пользователя",lang),reply_markup= await menu.cancel_menu(lang))
        await Send_bonus_admin.id.set()
    else:
        pass

@dp.message_handler(content_types=['text'],state=Send_bonus_admin.id)
async def send_bonus_id(message: types.Message, state: FSMContext):
    lang = langdb.get_lang(message.from_user.id)
    if clientdb.user_exists(message.text):
        await state.update_data(id = message.text)
        await message.answer(await translate_text("Сколько отправить?",lang),reply_markup= await menu.cancel_menu(lang))
        await Send_bonus_admin.count.set()
    else:
        await message.answer(await translate_text("Неверный ID пользователя.\n\nОперация отменена.",lang))
        await state.finish()

@dp.message_handler(content_types=['text'],state=Send_bonus_admin.count)
async def send_bonus_count(message: types.Message, state: FSMContext):
    await state.update_data(count = int(message.text))
    data = await state.get_data()
    komu_id = data.get('id')
    count_bonus = data.get('count')
    lang = langdb.get_lang(message.from_user.id)
    clientdb.add_bonus(komu_id,count_bonus)
    await message.answer(await translate_text(f"✅ Вы успешно перевели {count_bonus} бонусов пользователю {komu_id}",lang))
    komu_lang = langdb.get_lang(komu_id)
    await client_bot.send_message(komu_id,await translate_text(f"🎁 Пользователь @{message.from_user.username} вам отправил {count_bonus} бонусов!",komu_lang))
    await state.finish()


@dp.message_handler(content_types=['text'], text=['🗡🎁 Снять бонусы', translate_text_sync('🗡🎁 Снять бонусы', 'en'), translate_text_sync('🗡🎁 Снять бонусы', 'lt'), translate_text_sync('🗡🎁 Снять бонусы', 'pl')])
async def payments_options(message: types.Message):
    lang = langdb.get_lang(message.from_user.id)
    if message.from_user.id == admin_id:
        await message.answer(await translate_text("Напишите ID пользователя",lang),reply_markup= await menu.cancel_menu(lang))
        await Delete_bonus_admin.id.set()
    else:
        pass

@dp.message_handler(content_types=['text'],state=Delete_bonus_admin.id)
async def send_bonus_id(message: types.Message, state: FSMContext):
    lang = langdb.get_lang(message.from_user.id)
    if clientdb.user_exists(message.text):
        await state.update_data(id = message.text)
        await message.answer(await translate_text("Сколько снять?",lang),reply_markup= await menu.cancel_menu(lang))
        await Delete_bonus_admin.count.set()
    else:
        await message.answer(await translate_text("Неверный ID пользователя.\n\nОперация отменена.",lang))
        await state.finish()

@dp.message_handler(content_types=['text'],state=Delete_bonus_admin.count)
async def send_bonus_count(message: types.Message, state: FSMContext):
    await state.update_data(count = int(message.text))
    data = await state.get_data()
    komu_id = data.get('id')
    count_bonus = data.get('count')
    lang = langdb.get_lang(message.from_user.id)
    clientdb.del_bonus(komu_id,count_bonus)
    await message.answer(await translate_text(f"✅ Вы успешно сняли {count_bonus} бонусов пользователю {komu_id}",lang))
    komu_lang = langdb.get_lang(komu_id)
    await client_bot.send_message(komu_id,await translate_text(f"У вас снят {count_bonus} бонусов!",komu_lang))
    await state.finish()


@dp.message_handler(content_types=['text'], text=['🚖 Водители рядом', translate_text_sync('🚖 Водители рядом', 'en'), translate_text_sync('🚖 Водители рядом', 'pl'), translate_text_sync('🚖 Водители рядом', 'lt')])
async def nearby_drivers(message: types.Message):
    lat_long = clientdb.get_client_lat_long(message.from_user.id)
    latitude,longtitude = lat_long[0], lat_long[1]
    driver_count = clientdb.get_nearby_active_drivers_count(latitude,longtitude)
    lang = langdb.get_lang(message.from_user.id)
    client_ban = clientdb.get_ifbanned_client(message.from_user.id)
    if client_ban == 0:
        if driver_count >= 5:
            await message.answer(await translate_text(f"Рядом с вами {driver_count} водителей", lang))
        elif driver_count == 1:
            await message.answer(await translate_text(f"Рядом с вами {driver_count} водитель", lang))
        else:
            await message.answer(await translate_text(f"Рядом с вами {driver_count} водителя", lang))
    else:
        await message.answer(await translate_text("🔒 Вы забанены", lang))

@dp.message_handler(content_types=['text'], text=['📍 Обновить текущее местоположение', translate_text_sync('📍 Обновить текущее местоположение', 'en'), translate_text_sync('📍 Обновить текущее местоположение', 'pl'), translate_text_sync('📍 Обновить текущее местоположение', 'lt')])
async def change_location(message: types.Message, state: FSMContext):
    lang = langdb.get_lang(message.from_user.id)
    ban_client = clientdb.get_ifbanned_client(message.from_user.id)
    if ban_client == 0:
        await message.answer(await translate_text("📍 Отправьте текущее местоположение\n\n<i>[💡 Подсказка] Нажмите на скрепку, потом на геоданные,и на картах отмечайте место откуда будете ехать\n<b>Если хотите быстрое определение текущего местоположения, можете нажать на кнопку который появился у вас внизу ввода текста.</b></i>", lang),reply_markup= await menu.location(lang))
        await Change_location.latitude.set()
    else:
        await message.answer(await translate_text("🔒 Вы забанены", lang))

@dp.message_handler(content_types=[types.ContentType.LOCATION],state=Change_location.latitude)
async def order_taxi_start(message: types.Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude
    await state.update_data(latitude=latitude, longitude=longitude)
    
    # Получение данных о водителе из состояния FSM
    data = await state.get_data()
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    location = await get_address(latitude,longitude)
    
    # Сохранение данных в базе данных
    try:
        clientdb.update_client_location(message.from_user.id,latitude,longitude,location)
    except:
        pass
    try:
        driverdb.update_driver_location(message.from_user.id,latitude,longitude,location)
    except:
        pass

    
    lang = langdb.get_lang(message.from_user.id)
    
    await message.answer(await translate_text(f"Данные сохранены.\n\nТеперь вы находитесь в {location}", lang),reply_markup= await menu.menu_client(lang))
    
    # Завершение состояния FSM
    await state.finish()
    await message.answer_location(latitude,longitude)


@dp.message_handler(content_types=['text'], text=['✏ Создать заказ', translate_text_sync('✏ Создать заказ', 'en'), translate_text_sync('✏ Создать заказ', 'pl'), translate_text_sync('✏ Создать заказ', 'lt')], is_driver=True)
async def order_taxi_start(message: types.Message, state: FSMContext):
    # Получение местоположения пользователя из базы данных
    telegram_id = message.from_user.id
    driver_status = driverdb.get_driver_status(telegram_id)
    driver_ban = clientdb.get_ifbanned_client(telegram_id)
    lang = langdb.get_lang(telegram_id)
    if driver_ban == 0:
        if driver_status == 'active':
            user_location = driverdb.get_driver_lat_long(message.from_user.id)
            if user_location:
                latitude, longitude = user_location
                await state.update_data(location=(latitude, longitude))
                await message.answer(await translate_text("Выберите тип поиска для определения место приезда",lang), reply_markup=await menu.poisk_type(lang))
            else:
                pass
        elif driver_status in ['busy','to_client']:
            await message.answer(await translate_text("Вы уже в заказе, завершите заказ чтобы начать новую.",lang))
        else:
            await message.answer(await translate_text("Вы уже в заказе, завершите заказ чтобы начать новую.",lang))
    else:
        await message.answer(await translate_text("🔒 Вы забанены", lang))


@dp.callback_query_handler(text_startswith="search_adres", state=None)
async def search_geo(call: types.CallbackQuery):
    lang = langdb.get_lang(call.from_user.id)
    await call.message.answer(await translate_text("Укажите адрес место отправки.",lang),reply_markup=await menu.cancel_menu(lang))
    await OrderTaxi.Destination.set()


@dp.callback_query_handler(text_startswith="search_geo", state=None)
async def search_geo(call: types.CallbackQuery):
    lang = langdb.get_lang(call.from_user.id)
    await call.message.answer(await translate_text("Отправьте место на карте место отправки.",lang), reply_markup=await menu.cancel_menu(lang))
    await OrderTaxi.Destination.set()

# Обработчик получения места назначения от пользователя
@dp.message_handler(content_types=[types.ContentType.LOCATION],state=OrderTaxi.Destination)
async def process_destination(message: types.Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude
    destination = [latitude, longitude]
    await state.update_data(Destination=destination)

    await state.update_data(latitude=latitude)
    await state.update_data(longitude=longitude)
    lang = langdb.get_lang(message.from_user.id)
    latitude = message.location.latitude
    longitude = message.location.longitude
    destination = [latitude, longitude]
    await state.update_data(Destination=destination)

    lang = langdb.get_lang(message.from_user.id)

    # Отправляем сообщение с запросом подтверждения
    await message.answer_location(latitude,longitude)
    confirm_text = await translate_text("Вы указали это место в качестве конечного пункта. Подтвердите или измените его.", lang)
    await message.answer(confirm_text, reply_markup=await menu.confirm_location(lang, latitude, longitude))

    # Ожидаем подтверждения или изменения местоположения
    await OrderTaxi.ConfirmDestination.set()

@dp.callback_query_handler(state=OrderTaxi.ConfirmDestination)
async def confirm_destination(call: types.CallbackQuery, state: FSMContext):
    if call.data == "confirm_location":
        # Если местоположение подтверждено
        lang = langdb.get_lang(call.from_user.id)
        await call.message.answer(await translate_text("Сколько мест в машине?", lang), reply_markup=await menu.cancel_menu(lang))
        await OrderTaxi.sits.set()
    elif call.data == "change_location":
        # Если местоположение нужно изменить
        lang = langdb.get_lang(call.from_user.id)
        await call.message.answer(await translate_text("Пожалуйста, укажите новое место назначения.", lang), reply_markup=await menu.poisk_type(lang))
        await state.finish()

@dp.message_handler(content_types=['text'],state=OrderTaxi.sits)
async def process_destination(message: types.Message, state: FSMContext):
    sits = message.text
    lang = langdb.get_lang(message.from_user.id)
    try:
        sits = int(sits)
        if sits <= 18 or sits >= 4:
            await state.update_data(sits=sits)
            await message.answer(await translate_text("Введите дату и назначенное время в формате ГГГГ-ММ-ДД ЧЧ:ММ, и убедитесь, что оно в пределах следующих 36 часов. (например, 2024-05-18 15:30):",lang),reply_markup= await menu.cancel_menu(lang))
            await OrderTaxi.time.set()
        elif sits < 4:
            await message.answer(await translate_text("Минимальное кол-во мест 4",lang))
            await OrderTaxi.sits.set()
        else:
            await message.answer(await translate_text("Максимальное кол-во мест 18",lang))
            await OrderTaxi.sits.set()
    except:
        await message.answer(await translate_text("Напишите целое число!",lang))
        await OrderTaxi.sits.set()


@dp.message_handler(content_types=['text'],state=OrderTaxi.Destination)
async def process_destination(message: types.Message, state: FSMContext):
    location = message.text
    req = search_place_by_address(location)
    lang = langdb.get_lang(message.from_user.id)
    if req:
        latitude, longitude = req[1], req[0]

        destination = [latitude, longitude]
        await state.update_data(Destination=destination)

        await state.update_data(latitude=latitude)
        await state.update_data(longitude=longitude)

        # Получение данных о местоположении и месте назначения
        data = await state.get_data()
        destination = data.get('Destination')

        dest_location = await get_address(destination[0], destination[1])
        dest_locationn = str(dest_location)
        await state.update_data(Destination=dest_locationn)
        client_latlong = clientdb.get_client_lat_long(message.from_user.id)
        kilometers = await haversine_distance(client_latlong[0], client_latlong[1], destination[0], destination[1])
        # Ожидаем подтверждения или изменения местоположения
        await message.answer_location(latitude,longitude)
        confirm_text = await translate_text("Вы указали это место в качестве конечного пункта. Подтвердите или измените его.", lang)
        await message.answer(confirm_text, reply_markup=await menu.confirm_location(lang, latitude, longitude))
        await OrderTaxi.ConfirmDestination.set()
    else:
        await message.answer(await translate_text("❌ Не удалось определить место отправки.\n\nЗаказ отменен.",lang),reply_markup= await menu.menu_client(lang))
        await state.finish()
    

@dp.message_handler(content_types=['text'], state=OrderTaxi.time)
async def process_destination(message: types.Message, state: FSMContext):
    await state.update_data(time=message.text)
    # Получение данных о местоположении и месте назначения
    data = await state.get_data()
    destination = data.get('Destination')
    time_order = data.get('time')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    sits = data.get('sits')
    lang = langdb.get_lang(message.from_user.id)
    
    try:
        # Проверка времени заказа на корректность и диапазон
        if await is_order_time_valid_async(time_order):
            location_client = str(driverdb.get_location_driver(message.from_user.id)[0])
            dest_location = await get_address(latitude, longitude)
            dest_locationn = str(dest_location)
            await state.update_data(Destination=dest_locationn)
            client_latlong = driverdb.get_driver_lat_long(message.from_user.id)
            kilometers = await haversine_distance(client_latlong[0], client_latlong[1], latitude, longitude)
            time = await travel_time(client_latlong[0], client_latlong[1], latitude, longitude)
            bonus = calculate_bonuses(calculate_cost(round(kilometers, 2)))
            await state.update_data(bonus=bonus)
            
            # Подтверждение заказа и вывод информации
            message_text = (
                "🚖 **Вы создали маршрут**\n\n"
                "📍 **Откуда:**\n"
                f"{location_client}\n\n"
                "🏁 **Куда:**\n"
                f"{dest_locationn}\n\n"
                f"🕒 **Назначенное время:** {time_order}\n\n"
                f"📏 **Расстояние:** {round(kilometers, 2)} км\n"
                f"⏱ **Время поездки:** {time}\n\n"
                f"🙋‍♂️ **Свободных мест:** {sits}\n\n"
                f"💰 Стоимость {calculate_cost(round(kilometers, 2))} Руб.\n\n"
                f"🎁 Бонусы для оплаты {bonus}\n\n"
                "👉 Подтвердить заказ?"
            )
            await message.answer(await translate_text(message_text, lang), reply_markup=await menu.confirm_keyboard(lang))
            await message.answer_location(latitude, longitude)
            
            # Переход к следующему состоянию
            await OrderTaxi.Confirm.set()
        else:
            # Если время заказа не в допустимом диапазоне или имеет неверный формат
            await message.answer(await translate_text("Неверный формат даты и времени или время заказа вне допустимого диапазона.\nПожалуйста, введите дату и время в формате ГГГГ-ММ-ДД ЧЧ:ММ, и убедитесь, что оно в пределах следующих 36 часов.",lang),
                reply_markup=await menu.menu_client(lang)
            )
            await OrderTaxi.time.set()

    except Exception as e:
        # Обработка возможных ошибок
        await message.answer(
            translate_text("Неверный формат даты и времени или время заказа вне допустимого диапазона.\nПожалуйста, введите дату и время в формате ГГГГ-ММ-ДД ЧЧ:ММ, и убедитесь, что оно в пределах следующих 36 часов.",lang),
            reply_markup=await menu.menu_client(lang)
        )
        await OrderTaxi.time.set()

# Обработчик подтверждения заказа
@dp.message_handler(state=OrderTaxi.Confirm)
async def process_confirmation(message: types.Message, state: FSMContext):
    lang = langdb.get_lang(message.from_user.id)
    if message.text.lower() in ['да', 'yes', translate_text_sync('да','pl'), translate_text_sync('да','lt')]:
        await message.answer(await translate_text("Заказ принят.", lang),reply_markup= await menu.menu_client(lang))
        # Получение данных о заказе из состояния FSM
        data = await state.get_data()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        destination = data.get('Destination')
        sits = data.get('sits')
        location = [latitude,longitude]
        location_driver = driverdb.get_driver(message.from_user.id)
        location_driver = [location_driver[5], location_driver[6]]
        time = data.get('time')
        bonus = data.get('bonus')
        # Отправка заказа ближайшим водителям
        await send_order_to_nearest_clients(location_driver=location_driver,location=location,driver_id=message.from_user.id,destination = destination, lang_client=lang,datetime_str=time,sits=sits,bonus=bonus)
        await state.finish()
    else:
        lang = langdb.get_lang(message.from_user.id)
        await message.answer(await translate_text("Заказ отменен.", lang),reply_markup= await menu.menu_client(lang))
        await state.finish()

@dp.callback_query_handler(text_startswith="messages", state=None, is_driver=True)
async def view_messages(call: types.CallbackQuery):
    lang = langdb.get_lang(call.from_user.id)
    # Получите текущее местоположение водителя
    driver_location = driverdb.get_driver_lat_long(call.from_user.id)
    if driver_location:
        driver_latitude, driver_longitude = driver_location[0], driver_location[1]
        # Получите все заказы рядом с текущим местоположением водителя
        nearby_orders = orderdb.get_nearby_orders_for_driver(driver_latitude, driver_longitude)
        if nearby_orders:
            for order in nearby_orders:
                # Сообщение о заказе с кнопкой подтверждения
                client_location = clientdb.get_client_lat_long(order[1])
                await taxi_bot.send_location(
                    chat_id=call.from_user.id,
                    latitude=client_location[0],
                    longitude=client_location[1]
                )
                await taxi_bot.send_message(
                    chat_id=call.from_user.id,
                    text=await translate_text(f'''Клиент находится здесь 👆\n\n№{order[0]} - {order[1]}: {order[3]}.\nСтатус: {'Ожидает принятия' if order[4] == 'pending' else 'принят'}\n\n🕒 Назначенное время заказа {order[9]}''', lang),
                    reply_markup=await menu.confirm_order(order[0],lang)
                )
        else:
            await taxi_bot.send_message(call.from_user.id, translate_text_sync("Нет заказов рядом с вами.", lang))
    else:
        await taxi_bot.send_message(call.from_user.id, translate_text_sync("Не удалось определить ваше текущее местоположение.", lang))


@dp.callback_query_handler(text_startswith="confirmorder", state=None, is_driver=True) 
async def accept_order(call: types.CallbackQuery):
    lang = langdb.get_lang(call.from_user.id)
    try:
        order_id = call.data.split(',')[1]
        order_details = orderdb.get_order_details(order_id)

        if order_details[4] == 'pending':
            # Обновите статус заказа на "принят"
            orderdb.update_order_status(order_id, 'accepted')
            # Обновите статус водителя на "занят"
            driverdb.update_driver_status(call.from_user.id, 'active')
            # Удаляем сообщение о заказе
            await call.message.delete()
            # Ставим водителя на ордер
            orderdb.set_driver_order(order_id, call.from_user.id)
            await taxi_bot.send_message(chat_id=call.from_user.id, text=await translate_text(f"Клиент находится тут👆\n\nВы успешно приняли заказ №{order_id}\n\n🕒 Назначенное время {order_details[9]}", lang),reply_markup= await menu.driver_here(order_details[1],lang,call.from_user.id))
            client_lang = langdb.get_lang(order_details[1])
            driver_name = driverdb.get_driver(call.from_user.id)
            await client_bot.send_message(order_details[1],text=await translate_text(f"✅ Водитель {driver_name[2]}  {driver_name[13]} принял(-а) ваш заказ, водитель приедет в назначенное время",client_lang))
            clientdb.update_status_client_to_in_order(order_details[1])
        else:
            await call.answer(await translate_text("Невозможно принять заказ. Заказ уже принят или не существует.", lang))
            await call.message.delete()
    except (ValueError, TypeError):
        await call.answer(await translate_text('Невозможно принять заказ. Заказ уже принят или не существует.', lang))
        await call.message.delete()


@dp.callback_query_handler(text_startswith="confirmtempord", state=None, is_driver=True)
async def accept_order(call: types.CallbackQuery):
    lang = langdb.get_lang(call.from_user.id)
    input_tuple = call.data.split(',')[1:]


    int_list = [int(input_tuple[0].strip('[').strip())] + \
               [int(elem.strip()) for elem in input_tuple[1:-1]] + \
               [int(input_tuple[-1].strip(']').strip())]

    order_ids = int_list.copy()


    for order_id in order_ids:
        temp_order_details = tempordersdb.get_order(order_id)
        orderdb.add_order(
            temp_order_details[1],
            temp_order_details[2],
            temp_order_details[3],
            temp_order_details[4],
            temp_order_details[5],
            temp_order_details[6],
            temp_order_details[7],
            driver_id=call.from_user.id,
            bonus=temp_order_details[8]
        )
        tempordersdb.del_order(order_id)


        driver_name = driverdb.get_driver(call.from_user.id)
        await client_bot.send_message(
            temp_order_details[1],
            f'✅ Водитель {driver_name[2]}  {driver_name[13]} принял(-а) ваш заказ, водитель приедет в назначенное время'
        )

    # Update the driver status to "active"
    driverdb.update_driver_status(call.from_user.id, 'active')

    # Delete the message and notify the driver
    await call.message.delete()
    await call.message.answer(
        await translate_text(
            f"Заказ прикреплен к вашему аккаунту.\n\n<i>[💡 Подсказка] Нажмите на кнопку 'Текущий заказ'</i>", lang
        ),
        reply_markup=await menu.menu_driver(lang),
        parse_mode='html'
    )

    

@dp.callback_query_handler(text_startswith="declinetempord", state=None, is_driver=True)
async def accept_order(call: types.CallbackQuery):
    await call.message.delete()


@dp.callback_query_handler(text_startswith="driverhere", state=None, is_driver=True) 
async def accept_order(call: types.CallbackQuery):
    lang = langdb.get_lang(call.from_user.id)
    client_id = call.data.split(',')[1]
    driver_id = call.data.split(',')[2]
    lang_client = langdb.get_lang(client_id)
    await call.message.answer(await translate_text("Ожидайте клиента.",lang))
    driverdb.update_driver_status(call.from_user.id, 'busy')
    driver_details = driverdb.get_driver_car_details(driver_id)
    driver_name = driverdb.get_driver(driver_id)
    await client_bot.send_message(client_id, await translate_text(f"Водитель {driver_name[2]} {driver_name[13]} на месте.\n\nМашина: {driver_details[0]}\nНомер: {driver_details[1]}",lang_client))
    await call.message.delete()
    try:
        current_order = taxiorderdb.get_order(call.from_user.id)
        order_client = orderdb.get_order_by_client_id(client_id)
        await call.message.answer(await translate_text("Локация приезда",lang))
        await call.message.answer_location(current_order[3], current_order[4], reply_markup=await menu.complete_order(order_client[0],lang))
    except:
        current_orders = orderdb.get_current_order_for_driver(call.from_user.id)
        if current_orders:
            for current_order in current_orders:
                client_location = clientdb.get_client_lat_long(current_order[1])
                name = clientdb.get_client_name(current_order[1])[0]
                username = clientdb.get_client(current_order[1])[12]
                await call.message.answer(await translate_text(f"Текущий заказ:\n№{current_order[0]} - {name}  {username}: {current_order[3]}.\n\n"
                                    f"📃 Статус: принят.\n\n⏱ Время: {current_order[9]}", lang))
                driver_status = driverdb.get_driver_status(call.from_user.id)
                if driver_status == 'to_client' or driver_status == 'active':
                    await call.message.answer(await translate_text(f"Место клиента <b>{name}</b>  {username}",lang))
                    await taxi_bot.send_location(
                        chat_id=call.message.from_user.id,
                        latitude=client_location[0],
                        longitude=client_location[1],
                        reply_markup=await menu.driver_here(current_order[1],lang,call.message.from_user.id)
                    )
                
                elif driver_status == 'busy':
                    await call.message.answer(await translate_text(f"Место приезда клиента <b>{name}</b>  {username}",lang))
                    await call.message.answer_location(current_order[5],
                                                current_order[6],
                                                reply_markup=await menu.complete_order(current_order[0],lang)
                                                )

    try:
        current_order = orderdb.get_order_by_cc_id(client_id)
        if current_order[5] is not None and current_order[6] is not None:
            client_name = clientdb.get_client_name(client_id)
            username = clientdb.get_client(client_id)
            await call.message.answer(await translate_text(f"Локация приезда клиента <b>{client_name[0]}</b>  {username}",lang))
            await call.message.answer_location(current_order[5],
                                                current_order[6],
                                                reply_markup=await menu.complete_order(current_order[0],lang)
                                                )
        else:
            return '[-1373] pass'
    except:
        return '[-1375] pass'

@dp.callback_query_handler(text_startswith='complete_order', state=None, is_driver=True)
async def complete_order(call: types.CallbackQuery):
    lang = langdb.get_lang(call.from_user.id)
    order_id = call.data.split(',')[1]
    order_details = orderdb.get_order_details(order_id)
    taxiorder = taxiorderdb.get_order(call.from_user.id)
    if order_details[2] == call.from_user.id and order_details[4] == 'to_client_from_taxi' and taxiorder[8] == 'available':
        # Обновите статус заказа на "выполнен"
        orderdb.update_order_status(order_id, 'completed')
        client_name = clientdb.get_client_name(order_details[1])
        await call.message.delete()
        await call.message.answer(await translate_text(f"✅Вы успешно завершили заказ для клиента {client_name[0]}.\nБонусы от пользователя переведены на ваш счет", lang))
        client_lang = langdb.get_lang(order_details[1])
        await client_bot.send_message(order_details[1],text=await translate_text("✅ Ваш заказ завершен, спасибо за поездку!",client_lang))
        clientdb.del_bonus(order_details[1], taxiorder[13])
        clientdb.add_bonus(call.from_user.id,taxiorder[13])
        clientdb.update_status_client_to_active(order_details[1])
        loc_driver = await get_address(latitude=order_details[5],longitude=order_details[6])
        driverdb.update_driver_location(call.from_user.id,order_details[5],order_details[6],loc_driver)
        clientdb.update_client_location(order_details[1],order_details[5],order_details[6],loc_driver)
        sits = int(taxiorder[9])
        counter = 0
        counter += 1
        if counter == sits:
            taxiorderdb.finish_order(taxiorder[0])
            # Обновите статус водителя на "свободен"
            driverdb.update_driver_status(call.from_user.id, 'active')
            await taxi_bot.send_message(call.from_user.id,await translate_text(f"✅ Вы успешно завершили заказ №{taxiorder[0]}",lang))

            counter = 0
    else:
        order_id = call.data.split(',')[1]
        order_details = orderdb.get_order_details(order_id)

        if order_details[2] == call.from_user.id and order_details[4] == 'accepted':
            # Обновите статус заказа на "выполнен"
            orderdb.update_order_status(order_id, 'completed')
            # Обновите статус водителя на "свободен"
            driverdb.update_driver_status(call.from_user.id, 'active')
            await call.message.delete()
            await call.message.answer(await translate_text(f"✅ Вы успешно завершили заказ №{order_id}.\nБонусы автоматически переведены на ваш счет!", lang))
            client_lang = langdb.get_lang(order_details[1])
            await client_bot.send_message(order_details[1],text=await translate_text("✅ Ваш заказ завершен, спасибо за поездку!\n\nБонусы переведены!",client_lang))
            clientdb.add_bonus(call.from_user.id,order_details[10])
            clientdb.del_bonus(order_details[1],order_details[10])
            clientdb.update_status_client_to_active(order_details[1])
            loc_driver = await get_address(latitude=order_details[5],longitude=order_details[6])
            driverdb.update_driver_location(call.from_user.id,order_details[5],order_details[6],loc_driver)
            clientdb.update_client_location(order_details[1],order_details[5],order_details[6],loc_driver)

# Обработчик для просмотра информации о текущем заказе водителя
@dp.message_handler(content_types=['text'], text=['📝 Текущий заказ', translate_text_sync('📝 Текущий заказ', 'en'), translate_text_sync('📝 Текущий заказ', 'pl'), translate_text_sync('📝 Текущий заказ', 'lt')], state=None, is_driver=True)
async def current_order(message: types.Message):
    lang = langdb.get_lang(message.from_user.id)
    ban_driver = driverdb.get_ifbanned_driver(message.from_user.id)
    if ban_driver == 0:
        if_taxi_ord = taxiorderdb.if_driver_in_taxi_order(message.from_user.id)
        
        if if_taxi_ord:
            current_order = orderdb.get_current_order_from_driver(message.from_user.id)
            order_details = taxiorderdb.get_order(message.from_user.id)
            driver = driverdb.get_driver(message.from_user.id)
            kilometers = await haversine_distance(driver[5], driver[6], order_details[3], order_details[4])
            time = await travel_time(driver[5],driver[6], order_details[3], order_details[4])
            message_text = (
            f"🚖 **Текущий заказ: №{order_details[0]}**\n\n"
            "📍 **Откуда:**\n"
            f"{driver[7]} (В основу взят ваша)\n\n"
            "🏁 **Куда:**\n"
            f"{order_details[2]}\n\n"
            f"🕒 **Назначенное время:** {order_details[7]}\n\n"
            f"📏 **Расстояние:** {round(kilometers, 2)} км\n"
            f"⏱ **Время поездки:** {time}\n\n"
            f"🙋‍♂️ **Свободных мест:** {order_details[9]}\n\n"
            f"💰 Стоимость {calculate_cost(round(kilometers, 2))}\n"
            f"🎁 Бонусы для оплаты {order_details[13]}\n\n"
            f"Для того чтобы посмотреть места пользователей в заказе, нажмите на кнопки ниже 👇"
            )
            await message.answer(text=await translate_text(message_text,lang),reply_markup= await menu.get_client_locations(order_details[11]))
            await message.answer_location(order_details[3],order_details[4])
        else:
            # Получите текущий заказ водителя
            current_orders = orderdb.get_current_order_for_driver(message.from_user.id)
            if current_orders:
                for current_order in current_orders:
                    client_location = clientdb.get_client_lat_long(current_order[1])
                    name = clientdb.get_client_name(current_order[1])[0]
                    username = clientdb.get_client(current_order[1])[12]
                    await message.answer(await translate_text(f"Текущий заказ:\n№{current_order[0]} - {name}: {current_order[3]}.\n\n"
                                        f"📃 Статус: принят.\n\n⏱ Время: {current_order[9]}", lang))
                    driver_status = driverdb.get_driver_status(message.from_user.id)
                    if driver_status == 'to_client' or driver_status == 'active':
                        await message.answer(await translate_text(f"Место клиента {name}  {username}",lang))
                        await taxi_bot.send_location(
                            chat_id=message.from_user.id,
                            latitude=client_location[0],
                            longitude=client_location[1],
                            reply_markup=await menu.driver_here(current_order[1],lang,message.from_user.id)
                        )
                    
                    elif driver_status == 'busy':
                        await message.answer(await translate_text(f"Место приезда клиента {name}  {username}",lang))
                        await message.answer_location(current_order[5],
                                                    current_order[6],
                                                    reply_markup=await menu.complete_order(current_order[0],lang)
                                                    )
        # except:
        #     await message.answer(await translate_text("Вы не выполняете текущих заказов.", lang))
    else:
        await message.answer(await translate_text("🔒 Вы забанены", lang))


@dp.callback_query_handler(text_startswith="ordfromtaxi", state=None)
async def view_client_information(call: types.CallbackQuery):
    client_id = call.data.split(",")[1]
    lang = langdb.get_lang(call.from_user.id)
    info = clientdb.get_client_lat_long(client_id)
    await call.message.answer_location(latitude=info[0],longitude=info[1])
    await call.message.answer(text=await translate_text("Клиент находится тут 👆",lang),reply_markup= await menu.driver_here(client_id,lang,call.from_user.id))


@dp.message_handler(commands=['route'])
async def handle_route_command(message: types.Message):
    await message.answer("Отправьте стартовую позицию")
    await Adress.adress1.set()



@dp.message_handler(content_types=[types.ContentType.LOCATION], state=Adress.adress1)
async def handle_location_1(message: types.Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude
    address_1 = [latitude,longitude]
    await state.update_data(address1=address_1)
    await message.answer("Отправьте конечную точку")
    await Adress.adress2.set()

@dp.message_handler(content_types=[types.ContentType.LOCATION], state=Adress.adress2)
async def handle_location_2(message: types.Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude
    address_2 = [latitude,longitude]
    await state.update_data(address2=address_2)
    data = await state.get_data()
    start = data.get('address1')
    end = data.get('address2')
    url = route_google(start,end)
    await message.answer(f"Ссылка маршрута\n{url}")
    await state.finish()


if __name__ == '__main__':
    if not os.path.exists('avatars'):
        os.makedirs('avatars')
    if not os.path.exists('driver_license_photos'):
        os.makedirs('driver_license_photos')
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
    dp.middleware.setup(ThrottlingMiddleware())