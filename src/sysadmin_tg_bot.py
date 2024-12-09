#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 27 11:42:34 2024

@author: askh
"""

import aiohttp
import argparse
import asyncio
from dotenv import dotenv_values
import logging
import os
import re
import subprocess
import sys
import typing
from urllib.parse import urlparse
# import whois
import yaml

from aiogram import Bot, Dispatcher, html, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, \
    Message, \
    KeyboardButton, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove
from aiogram.types.link_preview_options import LinkPreviewOptions
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

from request_limit import RequestLimit
from host_check import HostChecker

HELP_TEXT = """\
Бот для сисадмина.

/help - вывод данной инструкции

/http_headers - показ заголовков HTTP сайта. После ввода команды вводите \
далее адреса сайтов по одному, в формате вида example.com, по умолчанию \
обращение идёт по протоколу HTTPS, можно указать адрес в формате \
http://example.com для проверки незащищённого соединения

/whois - показ информации WHOIS о сайтах. После ввода команды вводите имена\
доменов по одному, без указания протокола, порта и т.д., например: example.com

/cancel - отменить предыдущую команду (например, перестать выполнять команду) \
whois для вводимых имён доменов)\
"""

DEFAULT_CONFIG_FILE = 'sysadmin-tg-bot.yaml'

DOTENV_FILE = '.env'

PROG_NAME = 'sysadmin-tg-bot'


class UserState(StatesGroup):

    command = State()

    whois_host = State()

    smtp_relay_host = State()

    man_name = State()

    http_headers_host = State()


DOMAIN_NAME_LETTERS = r'a-zа-яё-'
DOMAIN_NAME_CHARS = r'0-9' + DOMAIN_NAME_LETTERS

# Bracket expressions for this character sets
DOMAIN_NAME_LETTERS_BE = f"[{DOMAIN_NAME_LETTERS}]"
DOMAIN_NAME_CHARS_BE = f"[{DOMAIN_NAME_CHARS}]"

# DOMAIN_RE = \
#     re.compile(
#         f"\\A(?:{DOMAIN_NAME_CHARS_BE}+\\.)*{DOMAIN_NAME_CHARS_BE}+\\.?\\Z",
#         re.I)

IP4_RE = re.compile(r'\A(\d+\.){3}\d\Z')
IP6_RE = re.compile(r'\A[0-9a-f:]+\Z', re.I)

SITE_RE = re.compile(
    r'\A(http(?:s)?://)?' +
    f"((?:{DOMAIN_NAME_CHARS_BE}+\\.)*{DOMAIN_NAME_CHARS_BE}+)" +
    r'(:\d+)?/?\Z', re.I)

DOMAIN_NAME_MAX_LENGTH = 2048  # Максимально допустимая длина для домена

# Максимально допустимая длина для адреса сайта
# (например, https://example.com:65535/ - то есть, протокол, адрес,
# возможно порт, возможно адрес /, но без адресов страниц и параметров GET)
SITE_URL_MAX_LENGTH = \
    DOMAIN_NAME_MAX_LENGTH + len('https://') + len(':65535') + len('/')

# Отделяем заголовок HTTP
HTTP_HEADERS_RE = re.compile(r'\A(.+?)(?:\r?\n){2}')

# Максимально допустимый размер заголовков HTTP
HTTP_HEADERS_MAX_LENGTH = 2048


# def check_host_name(name: str) -> bool:
#     """
#     Проверка допустимости имени хоста

#     Parameters
#     ----------
#     name : str
#         Имя хоста.

#     Returns
#     -------
#     bool
#         True, если имя хоста допустимо, если же нет, то False.

#     """
#     if len(name) > DOMAIN_NAME_MAX_LENGTH:
#         return False
#     if not re.match(DOMAIN_RE, name):
#         return False
#     return True


def check_site_url(url: str) -> bool:
    """
    Проверка допустимости адреса сайта. Адрес сайта -это доменное имя,
    возможно с префикстом http:// или https://, также возможно с номером
    порта и, возможно, оканчивающееся символом /. То есть, адрес сайта
    не содержит имя страницы (кроме корня сайта) и параметров GET, это
    не адрес страницы, а URL корня сайта.

    Parameters
    ----------
    url : str
        Адрес сайта.

    Returns
    -------
    bool
        True, если адрес сайта допустим, False в ином случае.

    """
    if len(url) > SITE_URL_MAX_LENGTH:
        return False
    if not SITE_RE.match(url):
        return False
    return True


# def create_menu_main_inline() -> InlineKeyboardMarkup:

#     ikb = InlineKeyboardBuilder()

#     button_whois = InlineKeyboardButton(text='whois',
#                                         callback_data='button_whois')
#     ikb.add(button_whois)

#     button_man = InlineKeyboardButton(text='man',
#                                       callback_data='button_man')
#     ikb.add(button_man)

#     return ikb.as_markup()


def create_menu_main() -> ReplyKeyboardMarkup:

    button_whois = KeyboardButton(text='/whois')

    # button_man = KeyboardButton(text='/man')

    button_http_headers = KeyboardButton(text='/http_headers')

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            # [button_man],
            [button_http_headers, button_whois]
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
    """
    Определяет имя сервера WHOIS для домена, используя whois-servers.net

    Parameters
    ----------
    domain : str
        Имя домена верхнего уровня, без точки.

    Returns
    -------
    str
        Имя сервера WHOIS, который может ответить на запросы о выбранном
        домене.

    """
    return domain + ".whois-servers.net"


# Коды ошибок
NO_ERROR = 0  # Ошибка отсутствует
ERROR_INCORRECT_VALUE = 1  # Было передано некорректное значение
ERROR_INTERNAL_ERROR = 2  # Внутренняя ошибка
ERROR_NO_DATA = 3  # Не были получены необходимые данные из внешнего источника
ERROR_DATA_TOO_BIG = 4  # Полученные данные слишком велики для того, чтобы
#                         дать ответ
ERROR_ACCESS_DENIED = 5  # Доступ запрещён

# Текстовые сообщения для ошибок при обработке команд
WHOIS_ERROR_MESSAGES = {
    ERROR_INCORRECT_VALUE: "Ошибка в имени хоста",
    ERROR_INTERNAL_ERROR: "Внутренняя ошибка",
    ERROR_NO_DATA: "Нет данных",
    ERROR_DATA_TOO_BIG: "Размер данных слишком большой",
    ERROR_ACCESS_DENIED: "Доступ запрещён"
}

DEFAULT_REQUEST_LIMIT_TIME_INTERVAL_SEC = 60
DEFAULT_REQUEST_LIMIT_FOR_ID = 2
DEFAULT_REQUEST_LIMIT_TOTAL = 10

# Объект для контроля за количеством запросов к боту
net_request_limit = None

# Объект для контроля корректности хостов и IP-адресов
host_checker = None

REQUEST_LIMIT_MESSAGE = "Достигнут лимит обращений, попробуйте повторить " + \
                        "запрос немного позднее"

# def get_whois_data_old(host: str) -> (str, int):

#     logger = logging.getLogger(__name__)

#     logger.debug("Whois for host: %s", host)

#     if not check_host_name(host):
#         return (None, ERROR_INCORRECT_VALUE)

#     text_data = ''
#     try:
#         w = whois.whois(host, command=True)
#     except whois.parser.PywhoisError as e:
#         logger.error(e)
#         return (None, ERROR_INTERNAL_ERROR)

#     w_dict = dict(w)
#     used_keys = set()

#     fields = ['domain_name', 'registrar', 'creation_date', 'expiration_date',
#               'name_servers', 'status', 'emails', 'org']
#     fields.extend(w_dict.keys())

#     for k in fields:
#         if k not in used_keys and k in w_dict:
#             used_keys.add(k)
#             if w_dict[k] is not None:
#                 text_data += str(k) + ": " + data_to_str(w_dict[k]) + "\n"

#     if text_data == '':
#         return (None, ERROR_NO_DATA)
#     return (text_data, NO_ERROR)


def get_whois_data(host: str) -> (str, int):

    logger = logging.getLogger(__name__)

    logger.debug("Whois for host: %s", host)

    if not host_checker.ok(host):
        return (None, ERROR_INCORRECT_VALUE)

    text_data = ''
    try:
        with subprocess.Popen(['whois', host], stdout=subprocess.PIPE) as proc:
            text_data_b = proc.stdout.read()
            if text_data_b is None or len(text_data_b) == 0:
                return (None, ERROR_NO_DATA)
            text_data = text_data_b.decode('utf-8')
            return (text_data, NO_ERROR)
    except Exception as e:
        logger.error(e)
        return (None, ERROR_INTERNAL_ERROR)


dp = Dispatcher(storage=MemoryStorage())


async def whois_answer(message: Message,
                       text: str):
    user_id = message.from_user.id

    if net_request_limit.request(user_id):

        host = text

        (whois_text, error) = get_whois_data(host)

        if whois_text is None:
            if error == ERROR_INTERNAL_ERROR:
                logger = logging.getLogger(__name__)
                logger.error("Internal error for /whois for host %s", host)
            whois_text = WHOIS_ERROR_MESSAGES.get(error, "Неизвестная ошибка")

        whois_text = 'whois ' + host + "\n\n" + whois_text

        await message.reply(whois_text,
                            # reply_markup=create_menu_main(),
                            link_preview_options=LinkPreviewOptions(
                                is_disabled=True))

    else:
        await message.reply(REQUEST_LIMIT_MESSAGE)


async def http_headers_answer(message: Message,
                              text: str):

    logger = logging.getLogger(__name__)


    user_id = message.from_user.id

    if net_request_limit.request(user_id):

        site = text

        normalized_site = normalize_site(site)

        (headers_text, error) = await get_headers_data(normalized_site)

        if headers_text is None:
            if error == ERROR_INTERNAL_ERROR:
                logger.error("Internal error for /http_headers for site %s",
                             site)
            headers_text = WHOIS_ERROR_MESSAGES.get(error,
                                                    "Неизвестная ошибка")

        headers_text = \
            'Заголовки HTTP для сайта ' + normalized_site + ":\n\n" + \
            headers_text

        await message.reply(headers_text,
                            # reply_markup=create_menu_main(),
                            link_preview_options=LinkPreviewOptions(
                                is_disabled=True))
    else:
        await message.reply(REQUEST_LIMIT_MESSAGE)


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
    # await message.answer(HELP_TEXT, reply_markup=create_menu_main())
    await message.answer(HELP_TEXT)


@dp.message(Command('help'))
async def command_help_handler(message: Message) -> None:
    """Обрабатывает команду /start

    Parameters
    ----------
    message : Message
        Обрабатываемое сообщение

    Returns
    -------
    None
    """
    # await message.answer(HELP_TEXT, reply_markup=create_menu_main())
    await message.answer(HELP_TEXT)


@dp.message(Command('cancel'))
async def cmd_cancel_handler(message: Message, state: FSMContext):
    """Обрабатывает команду /cancel
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

    await message.answer('Команда отменена',
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(UserState.command)


@dp.message(Command('whois'))
async def cmd_whois_handler(message: Message,
                            command: CommandObject,
                            state: FSMContext):
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

    if command.args is None:
        await message.answer('Вводите имена хостов (по одному):',
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(UserState.whois_host)
    else:
        await whois_answer(message, command.args)
        await state.set_state(UserState.command)


@dp.message(Command('http_headers'))
async def cmd_http_headers_handler(message: Message,
                                   command: CommandObject,
                                   state: FSMContext):
    """
    Обрабатывает команду /http_headers

    Parameters
    ----------
    message : Message
        Сообщение с командой.
    state : FSMContext
        Состояние конечного автомата.

    Returns
    -------
    None.

    """

    if command.args is None:
        await message.answer('Вводите адреса (по одному, ' +
                             'по умолчанию предполагается https://):',
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(UserState.http_headers_host)
    else:
        await http_headers_answer(message, command.args)
        await state.set_state(UserState.command)


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

    await whois_answer(message, message.text)


def normalize_site(site: str) -> str:
    if re.match(r'http(?:s)?://', site) is None:
        site = 'https://' + site
        return site


async def get_headers_data(site: str) -> (str, int):

    global host_checker

    logger = logging.getLogger(__name__)

    logger.debug("HTTP headers for site %s", site)

    if not check_site_url(site):
        logger.warn("Incorrect site: %s", site)
        return (None, ERROR_INCORRECT_VALUE)

    headers_text = ''
    # async with aiohttp.ClientSession() as session:
    #     try:
    #         async with session.get(site, allow_redirects=False) as response:
    #             if response.status == 200:
    #                 for pair in response.raw_headers:
    #                     (header, value) = [b.decode() for b in pair]
    #                     headers_text += f'{header}: {value}\n'
    #             else:
    #                 logger.error("Request failed for site %s", site)
    #                 return (None, ERROR_NO_DATA)
    #             else:
    #                 logger.error("Request failed for site %s", site)
    #                 return (None, ERROR_NO_DATA)
    #     except aiohttp.ClientConnectionError as e:
    #         logger.error(e)
    #         return (None, ERROR_NO_DATA)

    try:
        site_parsed = urlparse(site)
        use_ssl = site_parsed.scheme == 'https'
        host = site_parsed.hostname
        port = site_parsed.port

        if not host_checker.ok(host):
            return (None, ERROR_INCORRECT_VALUE)

        if port is None:
            port = 443 if use_ssl else 80
        logger.debug('Connect data: %s %s %s', str(use_ssl), host, str(port))
        if not re.match(r'\A[a-z0-9.-]*\Z', host, re.I):
            host_parts = []
            for p in host.split('.'):
                if not re.match(r'\A[a-z0-9-]*\Z', p, re.I):
                    host_parts.append('xn--' + p.encode('punycode').decode())
                else:
                    host_parts.append(p)
            host = '.'.join(host_parts)

        request_text = f"GET / HTTP/1.1\r\nHost: {host}\r\n\r\n"
        logger.debug("Request text: %s", request_text)
        request_data = request_text.encode()
        reader, writer = \
            await asyncio.open_connection(host=site_parsed.hostname,
                                          port=port,
                                          ssl=use_ssl)
        writer.write(request_data)
        await writer.drain()
        lines = ''
        logger.debug('Start reading from stream from host: %s',
                     site_parsed.hostname)
        while line := await reader.readline():
            line_str = line.decode()
            logger.debug('Read line: %s', line_str)
            if re.match(r'\A\r?\n\Z', line_str):
                break
            lines += line_str
        writer.close()
        # await writer.wait_closed()
        headers_text = lines
        if len(headers_text) > HTTP_HEADERS_MAX_LENGTH:
            logger.error("HTTP headers are to big for site %s",
                         site)
            return (None, ERROR_DATA_TOO_BIG)
    except Exception as e:
        logger.error("Exception: " + str(e))
        return (None, ERROR_INTERNAL_ERROR)

    return (headers_text, NO_ERROR)


@dp.message(F.text, UserState.http_headers_host)
async def http_headers_host_handler(message: Message, state: FSMContext):
    """Обрабатывает очередное имя хоста для команды /http_headers
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

    await http_headers_answer(message, message.text)


async def main():
    """
    Главная функция программы

Returns
    -------
    None.
    """

    global net_request_limit
    global host_checker

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

    net_request_limit = RequestLimit(
        max_total_value=config.get('limit_max_total_value',
                                   DEFAULT_REQUEST_LIMIT_TOTAL),
        max_id_value=config.get('limit_max_id_value',
                                DEFAULT_REQUEST_LIMIT_FOR_ID),
        time_interval_sec=config.get('imit_time_interval_sec',
                                     DEFAULT_REQUEST_LIMIT_TIME_INTERVAL_SEC))

    host_checker = HostChecker(
        hostname_min_len=config.get('hostname_min_len', None),
        hostname_max_len=config.get('hostname_max_len', None),
        restricted_hostnames=config.get('restricted_hostnames', []),
        restricted_ipv4=config.get('restricted_ipv4', []),
        restricted_ipv6=config.get('restricted_ipv6', [])
        )

    bot = Bot(token=token)

    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
