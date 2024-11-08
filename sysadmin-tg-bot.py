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
import typing
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


DOMAIN_NAME_LETTERS = r'a-zа-яё-'
DOMAIN_NAME_CHARS = r'0-9' + DOMAIN_NAME_LETTERS
# Bracket expressions for this character sets
DOMAIN_NAME_LETTERS_BE = f"[{DOMAIN_NAME_LETTERS}]"
DOMAIN_NAME_CHARS_BE = f"[{DOMAIN_NAME_CHARS}]"

DOMAIN_RE = \
    re.compile(f"^(?:{DOMAIN_NAME_CHARS_BE}+\\.)*{DOMAIN_NAME_CHARS_BE}+\\.?$",
               re.I)

IP4_RE = re.compile(r'^(\\d+\\.){3}\\d$')
IP6_RE = re.compile(r'^[0-9a-f:]+$', re.I)

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


def data_to_str(data: typing.Any) -> str:
    if type(data) is list:
        data_str = (str(x) for x in data)
        return ", ".join(data_str)
    return str(data)


def whois_server_for_domain(domain: str) -> str:
    return domain + ".whois-servers.net"


# Коды ошибок
NO_ERROR = 0  # Ошибка отсутствует
ERROR_INCORRECT_VALUE = 1  # Было передано некорректное значение
ERROR_INTERNAL_ERROR = 2  # Внутренняя ошибка
ERROR_NO_DATA = 3  # Не были получены необходимые данные из внешнего источника

# Текстовые сообщения для ошибок при обработке команды /whois
WHOIS_ERROR_MESSAGES = {
    ERROR_INCORRECT_VALUE: "Ошибка в имени хоста",
    ERROR_INTERNAL_ERROR: "Внутренняя ошибка",
    ERROR_NO_DATA: "Нет данных"
}


def get_whois_data(host: str) -> (str, int):
    logger = logging.getLogger(__name__)
    logger.debug("Whois for host: %s", host)
    if not check_host_name(host):
        return (None, ERROR_INCORRECT_VALUE)

    # if IP4_RE.match(host) is None and IP6_RE.match(host) is None:
    #     top_domain_match = \
    #         re.match(r'(?<=\\.(' + DOMAIN_NAME_LETTERS_BE + ')', host)
    # if top_domain_match is not None:
    #     top_domain = top_domain_match.group(1)
    #     whois_server = whois_server_for_domain(top_domain)

    text_data = ''
    try:
        w = whois.whois(host, command=True)
    except whois.parser.PywhoisError as e:
        logger.error(e)
        return (None, ERROR_INTERNAL_ERROR)

    w_dict = dict(w)
    used_keys = set()

    fields = ['domain_name', 'registrar', 'creation_date', 'expiration_date',
              'name_servers', 'status', 'emails', 'org']
    fields.extend(w_dict.keys())

    for k in fields:
        if k not in used_keys and k in w_dict:
            used_keys.add(k)
            if w_dict[k] is not None:
                text_data += str(k) + ": " + data_to_str(w_dict[k]) + "\n"

    if text_data == '':
        return (None, ERROR_NO_DATA)
    return (text_data, NO_ERROR)


dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Обрабатывает команду /start

    Parameters
    ----------
    message : Message
        Обрабатываемое сообщение

    Returns
    -------
    None
    """
    await message.answer(HELP_TEXT, reply_markup=create_menu_main())


@dp.message(F.text.lower() == '/whois')
async def cmd_whois_handler(message: Message, state: FSMContext):
    """Обрабатывает команду /whois
    Parameters
    ----------
    message : Message
        Обрабатываемое сообщение.
    state : FSMContext
        Состояние конечного автомата.

    Returns
    -------
    None.
    """

    await message.answer('Вводите имена хостов (по одному):',
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(UserState.whois_host)


@dp.message(F.text, UserState.whois_host)
async def whois_host_handler(message: Message, state: FSMContext):
    """Обрабатывает очередное имя хоста для команды /whois
    Parameters
    ----------
    message : Message
        Обрабатываемое сообщение.
    state : FSMContext
        Состояние конечного автомата.

    Returns
    -------
    None.
    """

    host = message.text
    (whois_text, error) = get_whois_data(host)
    if whois_text is None:
        if error == ERROR_INTERNAL_ERROR:
            logger = logging.getLogger(__name__)
            logger.error("Internal error for /whois for host %", host)
        whois_text = WHOIS_ERROR_MESSAGES.get(error, "Неизвестная ошибка")
    whois_text = 'whois ' + host + "\n\n" + whois_text
    await message.reply(whois_text, reply_markup=create_menu_main())


async def main():
    """Главная функция программы

Returns
    -------
    None.
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

    logger = logging.getLogger(__name__)
    try:
        with open(options.config_file, 'r') as config_file:
            config = yaml.safe_load(config_file)
    except IOError as e:
        logger.error(f"Can't load the config file: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Can't parse the config file: {e}")
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
            logger.error(f"Config error, unknown token: {e}")
            sys.exit(1)

    if options.debug or config.get('debug') == 1:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    bot = Bot(token=token)

    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
