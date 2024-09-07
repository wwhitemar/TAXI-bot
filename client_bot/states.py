from aiogram.dispatcher.filters.state import State, StatesGroup

class Adress(StatesGroup):
    adress1 = State()
    adress2 = State()

class Client_Start(StatesGroup):
    name = State()
    phone = State()
    latitude_longitude = State()

class Chose_lang(StatesGroup):
    lang = State()

class Driver_Start(StatesGroup):
    lang = State()
    name = State()
    points = State()
    question1 = State()
    question2 = State()
    question3 = State()
    question4 = State()
    question5 = State()
    question_final = State()
    car = State()
    car_number = State()
    latitude_longitude = State()
    phone = State()
    voditel_prava = State()

class Change_location(StatesGroup):
    latitude = State()
    longitude = State()
    address = State()

class Change_location_from(StatesGroup):
    latitude = State()
    longitude = State()
    address = State()


class OrderTaxi(StatesGroup):
    otkuda = State()
    latitude = State()
    longitude = State()
    Destination = State()
    ConfirmDestination = State()
    time = State()
    Confirm = State()

class OrderTaxi_search(StatesGroup):
    location = State()
    Confirm = State()

class Banusr(StatesGroup):
    user = State()

class Unbanusr(StatesGroup):
    user = State()

class Addmoder(StatesGroup):
    user = State()

class Deletemoder(StatesGroup):
    user = State()

class Profile_photo(StatesGroup):
    photo = State()

class Change_name(StatesGroup):
    name = State()

class Change_lang(StatesGroup):
    lang = State()

class Send_bonus(StatesGroup):
    id = State()
    count = State()

class Send_bonus_admin(StatesGroup):
    id = State()
    count = State()

class Delete_bonus_admin(StatesGroup):
    id = State()
    count = State()

class ChangePaymentsOptions(StatesGroup):
    km = State()
    precent_bonus = State()