import os
import sys
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
from datetime import datetime,timedelta
from geopy.distance import geodesic
from geopy.distance import great_circle
import config
from databasee import *
import configparser
import asyncio
import googlemaps

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
tempordersdb = Temp_OrdersTable()

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


async def send_order_to_nearest_drivers(location_client, location, client_id, destination, lang_client, datetime_str, bonus):
    order_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    time_diff = (order_datetime - datetime.now()).total_seconds()
    latitude, longitude = location_client[0], location_client[1]
    search_radius = 0.05

    client_coord = clientdb.get_client_lat_long(client_id)
    nearby_drivers = clientdb.get_nearby_active_drivers(latitude, longitude, radius=search_radius)
    tempordersdb.add_order(client_id=client_id, destination=str(destination), latitude=location[0], longitude=location[1], client_latitude=client_coord[0], client_longitude=client_coord[1], datetime=datetime_str, bonus=bonus)
    
    nearpoints = tempordersdb.get_nearby_orders_in_range()

    if nearpoints and nearby_drivers:
        message_text = '🚖 Новый групповой заказ!\n\n'
        temporder_id = []

        for index, order_id in enumerate(nearpoints):
            user = tempordersdb.get_order(order_id)
            client_name = clientdb.get_client(user[1])
            message_text += f'''<b>[{index + 1}] клиент</b>\n
📃ФИО: {client_name[2]} - {client_name[12]}

Начальная точка: {client_name[5]}

Конечная точка: {user[2]}

Бонусы для оплаты: {user[8]}

⏱Время: {user[7]}\n\n'''
            temporder_id.append(order_id)

        for driver in nearby_drivers:
            driver_id = driver[0]
            lang = langdb.get_lang(driver_id)
            await taxi_bot.send_message(driver_id, await translate_text(message_text, lang), reply_markup=await keyboard.accept_temp_order(lang, temporder_id), parse_mode='html')

# Функция для вычисления расстояния между двумя точками
def calculate_distance(point1, point2):
    return geodesic(point1, point2).kilometers


# Функция для объединения ближайших заказов
def merge_orders(current_location, all_orders):
    nearby_orders = []
    for order in all_orders:
        distance = calculate_distance(current_location, (order[1], order[2]))
        if distance <= 1:
            nearby_orders.append(order)
    return nearby_orders

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

def are_points_near(coord1, coord2, radius=5):
    # Вычисляем расстояние между двумя координатами в километрах
    distance = great_circle(coord1, coord2).km
    return distance <= radius

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