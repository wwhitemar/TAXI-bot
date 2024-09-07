import subprocess
import logging
from aiogram import Dispatcher, Bot
from config import *
from aiogram.contrib.fsm_storage.memory import MemoryStorage

subprocess.Popen('python taxi_bot/bot.py')
subprocess.Popen('python client_bot/bot.py')

logging.basicConfig(level=logging.INFO)