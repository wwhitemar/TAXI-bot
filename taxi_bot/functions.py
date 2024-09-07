import os
import sys
import googlemaps.client
from databasee import *
import aiohttp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import Throttled

from aiogram.types import CallbackQuery
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.utils.exceptions import BotBlocked
from aiogram.dispatcher import filters
from aiogram.types import ChatType
from aiogram.types import InputFile
from aiogram.types import ReplyKeyboardRemove
import logging
from yandex_geocoder import Client
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
import menu as keyboard
from yandex_geocoder import Client as YandexGeocoder
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, timedelta
from geopy.distance import geodesic
from geopy.distance import great_circle
import config
import configparser
import asyncio
import googlemaps

async def schedule_order(order_datetime_str: str):
    order_datetime = datetime.strptime(order_datetime_str, "%Y-%m-%d %H:%M")
    time_diff = (order_datetime - datetime.now()).total_seconds()
    if time_diff > 0:
        await asyncio.sleep(time_diff)
    # Здесь можно добавить код для выполнения заказа

# Пример использования функции
order_datetime_str = "2024-08-22 22:22"
asyncio.run(schedule_order(order_datetime_str))

async def send_order_to_nearest_drivers(location_client, location, client_id, destination, lang_client, datetime_str):
    order_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    time_diff = (order_datetime - datetime.now()).total_seconds()
    if time_diff > 0:
        await asyncio.sleep(time_diff)
    # Здесь можно добавить код для выполнения заказа

logging.basicConfig(level=logging.INFO)

# env
load_dotenv()

API_TOKEN = config.API_TOKEN_CLIENT
YANDEX_GEOCODER_API_KEY = config.YANDEX_GEOCODER_API_KEY
GOOGLE_MAPS_API = config.GOOGLE_MAPS_API
# Инициализация бота и диспетчера
client_bot = Bot(token=API_TOKEN)
dp = Dispatcher(client_bot, storage=MemoryStorage())
taxi_bot = Bot(token=config.API_TOKEN_TAXI)



# Инициализация базы данных
clientdb = ClientDB()
driverdb = DriverDB()
orderdb = OrderDB()
langdb = LangDB()
taxiorderdb = Order_Taxi_DB()

def route_google(start,end):
    url = f"https://www.google.com/maps/dir/?api=1&origin={start[0]}+{start[1]}&destination={end[0]}+{end[1]}&travelmode=driveing"
    return url


async def get_address(latitude, longitude):
    async with aiohttp.ClientSession() as session:
        url = f"https://geocode-maps.yandex.ru/1.x/?apikey={YANDEX_GEOCODER_API_KEY}&format=json&geocode={longitude},{latitude}"
        async with session.get(url) as response:
            data = await response.json()
            address = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']
            return address

def translate_text_sync(text,lang):
    try:
        return GoogleTranslator(source='auto', target=lang).translate(text)
    except:
        return GoogleTranslator(source='auto', target=lang).translate_batch(text)
    
async def translate_text(text: str, lang: str) -> str:
    return await asyncio.to_thread(translate_text_sync, text, lang)

async def send_order_to_nearest_drivers(location_client,location, client_id, destination, lang_client,datetime_str):
    order_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")

    # Ожидание до указанного времени
    time_diff = (order_datetime - datetime.now()).total_seconds()
    # Получение координат местоположения заказа
    latitude, longitude = location_client[0], location_client[1]

    # Определение радиуса поиска водителей (в километрах)
    search_radius = 0.01  # Например, поиск водителей в радиусе 5 км от места заказа

    # Получение списка ближайших активных водителей

    client_coord = clientdb.get_client_lat_long(client_id)
    nearby_drivers = clientdb.get_nearby_active_drivers(latitude, longitude, radius=search_radius)
    if nearby_drivers:
        for driver in nearby_drivers:
            driver_id = driver[0]
            # Отправкения о новом заказе водителю
            lang = langdb.get_lang(driver_id)
            await taxi_bot.send_message(driver_id, translate_text("🚖 Новый заказ! Пожалуйста, проверьте свои сообщения для получения подробностей.", lang), reply_markup=keyboard.messages(lang))
        orderdb.add_order(client_id = client_id, destination = str(destination),latitude=location[0],longitude=location[1],client_latitude=client_coord[0],client_longitude=client_coord[1],datetime=datetime_str)
    else:
        await client_bot.send_message(client_id, translate_text("Нет активных водителей поблизости.\n\nЗаказ отменен.", lang_client), reply_markup=keyboard.menu_client(lang_client))


async def send_order_to_nearest_clients(location_driver, location, driver_id, destination, lang_client,datetime_str, sits, bonus):
    order_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")

    # Ожидание до указанного времени
    time_diff = (order_datetime - datetime.now()).total_seconds()
    # Получение координат местоположения заказа
    latitude, longitude = location_driver[0], location_driver[1]


    search_radius = 0.05 
    nearby_clients = driverdb.get_nearby_active_clients(latitude, longitude, radius=search_radius)
    if nearby_clients:
        taxiorderdb.create_order(driver_id=driver_id,destination=destination,latitude=location[0],longitude=location[1],driver_latitude=latitude,driver_longitude=longitude,pickup_time=datetime_str,sits=sits,bonus=bonus)
        order_id = taxiorderdb.get_order(driver_id)
        for client_id in nearby_clients:
            client = client_id[0]
            # Отправкения о новом заказе водителю
            lang = langdb.get_lang(client)
            await client_bot.send_message(client, await translate_text("🚖 Новый групповой заказ от таксиста!\n\nНажмите на кнопку который находится внизу для получения подробностей.", lang), reply_markup=await keyboard.generate_order_menu(order_id=order_id[0],lang=lang))
    else:
        await taxi_bot.send_message(driver_id, await translate_text("Нет активных клиентов поблизости.\n\nЗаказ отменен.", lang_client), reply_markup=await keyboard.menu_driver(lang_client))

def is_order_time_valid(time_order_str: str) -> bool:
    """
    синхронная функция для проверки, попадает ли указанное время заказа в допустимый диапазон (36 часов от текущего времени).
    
    :param time_order_str: Время заказа в формате строки "YYYY-MM-DD HH:MM".
    :return: True, если время заказа в пределах 36 часов от текущего времени, иначе False.
    """
    try:
        # Преобразуем строку времени в объект datetime
        order_time = datetime.strptime(time_order_str, "%Y-%m-%d %H:%M")
        
        # Получаем текущее время
        now = datetime.now()
        
        # Устанавливаем границы допустимого диапазона
        min_time = now
        max_time = now + timedelta(hours=36)
        
        # Проверяем, попадает ли время заказа в диапазон
        return min_time <= order_time <= max_time
    except ValueError:
        # Возвращаем False, если строка времени имеет неверный формат
        return False

async def is_order_time_valid_async(time_order_str) -> bool:
    """
    асинхронная функция для проверки, попадает ли указанное время заказа в допустимый диапазон (36 часов от текущего времени).
    
    :param time_order_str: Время заказа в формате строки "YYYY-MM-DD HH:MM".
    :return: True, если время заказа в пределах 36 часов от текущего времени, иначе False.
    """
    return await asyncio.to_thread(is_order_time_valid, time_order_str)


def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

def write_config(config):
    with open('config.ini', 'w') as configfile:
        config.write(configfile)



def calculate_cost(distance_km):
    """
    Функция для расчета стоимости поездки.
    
    :param distance_km: Количество километров
    :return: Общая стоимость поездки в рублях (целое число)
    """

    config = configparser.ConfigParser()
    config.read('config.ini')
    cost_per_km = float(config['Pricing']['cost_per_km'])
    total_cost = distance_km * cost_per_km
    return round(total_cost)

def calculate_bonuses(total_cost):
    """
    Функция для расчета суммы бонусов.

    :param total_cost: Общая стоимость поездки в рублях
    :return: Сумма бонусов (целое число)
    """
    config = configparser.ConfigParser()
    config.read('config.ini')
    bonus_percentage = float(config['Pricing']['max_bonus_percentage'])
    return round(total_cost * (bonus_percentage / 100))

def search_place_by_address(address):
    try:
        geocoder = YandexGeocoder(api_key=YANDEX_GEOCODER_API_KEY)
        full_address = f"{address}"
        response = geocoder.coordinates(full_address)
        if response:
            lat = float(response[0])
            lon = float(response[1])
            return lat, lon
        else:
            return False
    
    except Exception as e:
        return False

def haversine_distance_sync(lat1, lon1, lat2, lon2):
    """
    Calculate the travel distance and time between two locations using Google Maps API.

    Parameters:
    - origin: str, the starting address or latitude/longitude coordinates
    - destination: str, the destination address or latitude/longitude coordinates
    - mode: str, the mode of transport. Options are 'driving', 'walking', 'bicycling', 'transit'

    Returns:
    - distance: float, the distance between origin and destination in kilometers
    """

    # Request distance matrix from Google Maps API
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API)
    origin = (lat1, lon1)
    destination = (lat2, lon2)
    result = gmaps.distance_matrix(origins=origin, destinations=destination, mode='driving')

    # Extract distance and duration from the result
    distance = result['rows'][0]['elements'][0]['distance']['value'] / 1000.0  # in kilometers
    return distance

async def haversine_distance(lat1, lon1, lat2, lon2):
    return await asyncio.to_thread(haversine_distance_sync, lat1, lon1, lat2, lon2)


def travel_time_sync(lat1, lon1, lat2, lon2):
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API)
    origin = (lat1, lon1)
    destination = (lat2, lon2)
    result = gmaps.distance_matrix(origins=origin, destinations=destination, mode='driving')

    # Extract distance and duration from the result
    duration = result['rows'][0]['elements'][0]['duration']['value'] / 60.0
    return f"{int(duration)} min"

async def travel_time(lat1, lon1, lat2, lon2):
    return await asyncio.to_thread(travel_time_sync, lat1, lon1, lat2, lon2)

# Новая функция для проверки имени
def is_valid_name(name: str) -> bool:
    if len(name.split()) > 3:
        return False
    if any(char.isdigit() or not char.isalpha() for char in name.replace(" ", "")):
        return False
    return True

# Обработчик состояния для ввода имени
@dp.message_handler(state=Client_Start.name)
async def client_start_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    lang = langdb.get_lang(message.from_user.id)
    await message.answer(await translate_text("Как к вам обращаться?", lang))
    await Client_Start.nickname.set()

# Обработчик состояния для ввода никнейма
@dp.message_handler(state=Client_Start.nickname)
async def client_start_nickname(message: types.Message, state: FSMContext):
    nickname = message.text
    if not is_valid_name(nickname):
        await message.answer("Пожалуйста, введите корректное имя (максимум 3 слова, без символов и цифр).")
        return
    await state.update_data(nickname=nickname)
    lang = langdb.get_lang(message.from_user.id)
    await message.answer(await translate_text("Пожалуйста поделитесь своим номером.", lang), reply_markup=await menu.phone_share(lang))
    await Client_Start.phone.set()

# Обработчик состояния для ввода номера телефона
@dp.message_handler(content_types=[types.ContentType.CONTACT], state=Client_Start.phone)
async def phone_client(message: types.Message, state: FSMContext):
    lang = langdb.get_lang(message.from_user.id)
    contact = message.contact
    phone_number = contact.phone_number
    await state.update_data(phone=phone_number)
    await message.answer(await translate_text("Пожалуйста отправьте место отправки", lang), reply_markup=await menu.location(lang))
    await Client_Start.latitude_longitude.set()

# Обработчик состояния для ввода местоположения
@dp.message_handler(content_types=[types.ContentType.LOCATION], state=Client_Start.latitude_longitude)
async def client_start_location(message: types.Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude
    latitude_longitude = [latitude, longitude]
    await state.update_data(latitude_longitude=latitude_longitude)