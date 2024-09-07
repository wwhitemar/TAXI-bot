import subprocess
import logging
from aiogram import Dispatcher, Bot
from config import *
from aiogram.contrib.fsm_storage.memory import MemoryStorage

subprocess.run('python taxi_bot/bot.py &',shell=True)
subprocess.run('python client_bot/bot.py &',shell=True)

logging.basicConfig(level=logging.INFO)