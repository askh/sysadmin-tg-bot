#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 27 11:42:34 2024

@author: askh
"""

import argparse
import asyncio
from dotenv import dotenv_values
import logging
import os
import re
import subprocess
import sys
import whois
import yaml

from aiogram import Bot, Dispatcher, html, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, \
    Message, \
    KeyboardButton, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

HELP_TEXT = "Бот для сисадмина."

DEFAULT_CONFIG_FILE = 'sysadmin-tg-bot.yaml'

DOTENV_FILE = '.env'

PROG_NAME = 'sysadmin-tg-bot'


class UserState(StatesGroup):

    command = State()

    whois_host = State()

    smtp_relay_host = State()

    man_name = State()


DOMAIN_NAME_CHARS = r'[a-z0-9а-яё-]'

DOMAIN_RE = \
    re.compile(f"^(?:{DOMAIN_NAME_CHARS}+\\.)*{DOMAIN_NAME_CHARS}+\\.?$",
               re.I)
DOMAIN_NAME_MAX_LENGTH = 2048


def check_host_name(name: str) -> bool:
    if len(name) > DOMAIN_NAME_MAX_LENGTH:
        return False
    if not re.match(DOMAIN_RE, name):
        return False
    return True


def create_menu_main_inline() -> InlineKeyboardMarkup:

    ikb = InlineKeyboardBuilder()

    button_whois = InlineKeyboardButton(text='whois',
                                        callback_data='button_whois')
    ikb.add(button_whois)

    button_man = InlineKeyboardButton(text='man',
                                      callback_data='button_man')
    ikb.add(button_man)

    return ikb.as_markup()


def create_menu_main() -> ReplyKeyboardMarkup:

    button_whois = KeyboardButton(text='/whois')

    button_man = KeyboardButton(text='/man')

    button_smtp_relay = KeyboardButton(text='/smtp_relay')

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [button_man],
            [button_smtp_relay, button_whois]
        ],
        resize_keyboard=True,
        one_time_keyboard=True)

    return keyboard


def data_to_str(data):
    if type(data) is list:
        data_str = (str(x) for x in data)
        return ", ".join(data_str)
    return str(data)


async def get_whois_data(host: str) -> str:
    if not check_host_name(host):
        return None
    text_data = ''
    try:
        w = whois.whois(host)
    except whois.parser.PywhoisError as e:
        logging.error(e)
        return None

    w_dict = dict(w)
    used_keys = set()

    fields = ['domain_name', 'registrar', 'creation_date', 'expiration_date',
              'name_servers', 'status', 'emails', 'org']
    fields.extend(w_dict.keys())

    for k in fields:
        if k not in used_keys and k in w_dict:
            text_data += str(k) + ": " + data_to_str(w_dict[k]) + "\n"
            used_keys.add(k)

    return text_data


dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Parameters
    ----------
    message : Message
        Обрабатываемое сообщение

    Returns
    -------
    None
        Никакого результата не возвращается.

    Обрабатывает команду /start
    """
    await message.answer(HELP_TEXT, reply_markup=create_menu_main())


@dp.message(F.text.lower() == '/whois')
async def answer_cmd_whois(message: Message, state: FSMContext):

    await message.answer('Введите имя хоста',
                         reply_markup=ReplyKeyboardRemove())

    await state.set_state(UserState.whois_host)


@dp.message(F.text, UserState.whois_host)
async def answer_whois_host(message: Message, state: FSMContext):
    host = message.text
    whois_text = await get_whois_data(host)
    # await message.answer('whois ' + host)
    if whois_text is None:
        whois_text = 'Ошибка при получении данных'
    whois_text = 'whois ' + host + "\n\n" + whois_text
    await message.reply(whois_text, reply_markup=create_menu_main())


async def main():
    """

    Returns
    -------
    None.

    Главная функция программы
    """

    arg_parser = argparse.ArgumentParser(
        prog=PROG_NAME
        )

    arg_parser.add_argument('-c',
                            '--config',
                            type=str,
                            dest='config_file',
                            default=DEFAULT_CONFIG_FILE,
                            help='Config file.',
                            metavar='CONFIG_FILE')

    arg_parser.add_argument('-d',
                            '--debug',
                            action='store_true',
                            dest='debug',
                            default=False,
                            help='Debug mode.')

    options = arg_parser.parse_args()

    try:
        with open(options.config_file, 'r') as config_file:
            config = yaml.safe_load(config_file)
    except IOError as e:
        logging.error(f"Can't load the config file: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Can't parse the config file: {e}")
        sys.exit(1)

    env = {
        **dotenv_values(DOTENV_FILE),
        **os.environ,
    }

    token = env.get('TELEGRAM_TOKEN')
    if token is None:
        try:
            token = config['telegram_token']
        except KeyError as e:
            logging.error(f"Config error, unknown token: {e}")
            sys.exit(1)

    if options.debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Debug mode enabled")

    bot = Bot(token=token)

    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
