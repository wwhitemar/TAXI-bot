from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from databasee import *

driverdb = DriverDB()

class IsDriver(BoundFilter):
    key = 'is_driver'

    def __init__(self, is_driver):
        self.is_driver = is_driver

    async def check(self, message: types.Message) -> bool:
        driver = driverdb.check_driver_in_db(message.from_user.id)
        if driver:
            return self.is_driver
        else:
            return False