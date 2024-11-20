#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 16 19:19:49 2024

@author: askh
"""

import copy
import ipaddress
import logging
import re
from typing import Any


class HostChecker:

    DEFAULT_HOSTNAME_MIN_LEN = 1
    DEFAULT_HOSTNAME_MAX_LEN = 1024

    DOMAIN_NAME_LETTERS = r'a-zа-яё-'
    DOMAIN_NAME_CHARS = r'0-9' + DOMAIN_NAME_LETTERS

    # Bracket expressions for this character sets
    DOMAIN_NAME_LETTERS_BE = f"[{DOMAIN_NAME_LETTERS}]"
    DOMAIN_NAME_CHARS_BE = f"[{DOMAIN_NAME_CHARS}]"

    DOMAIN_RE = re.compile(
        f"\\A(?:{DOMAIN_NAME_CHARS_BE}+\\.)*{DOMAIN_NAME_CHARS_BE}+\\.?\\Z",
        re.I)

    IP4_RE = re.compile(r'\A(\d+\.){3}\d\Z')
    IP6_RE = re.compile(r'\A[0-9a-f:]+\Z', re.I)

    # Возможные результаты проверок адресов
    ADDRESS_OK = 0  # Проверка успешно прошла, адрес допустим и разрешён
    ADDRESS_INCORRECT = 1  # Адрес некорректен
    ADDRESS_DENIED = 2  # Адрес корректен, но доступ к нему запрещён

    def _change_none(self, val: Any, alt: Any) -> Any:
        if val is None:
            return alt
        else:
            return val

    def __init__(self,
                 hostname_min_len=None,
                 hostname_max_len=None,
                 restricted_hostnames=[],
                 restricted_ipv4=[],
                 restricted_ipv6=[]):
        logger = logging.getLogger(__name__)
        self.hostname_min_len = \
            self._change_none(hostname_min_len,
                              self.DEFAULT_HOSTNAME_MIN_LEN)
        self.hostname_max_len = \
            self._change_none(hostname_max_len,
                              self.DEFAULT_HOSTNAME_MAX_LEN)
        self.restricted_hostnames = copy.copy(restricted_hostnames)

        self.restricted_ipv4 = []
        for i in restricted_ipv4:
            try:
                ipv4 = ipaddress.ip_network(i)
                self.restricted_ipv4.append(ipv4)
            except ValueError:
                logger.error("Can't parse IPv4 address %s", i)

        self.restricted_ipv6 = []
        for i in restricted_ipv6:
            try:
                ipv6 = ipaddress.ip_network(i)
                self.restricted_ipv6.append(ipv6)
            except ValueError:
                logger.error("Can't parse IPv6 address %s", i)

    def check_len(self, name: str) -> bool:
        """
        Проверка длины имени хоста

        Parameters
        ----------
        name : str
            Имя хоста.

        Returns
        -------
        bool
            True, если длина имени допустима, в ином случае False.

        """
        name_len = len(name)
        return name_len >= self.hostname_min_len and \
            name_len <= self.hostname_max_len

    def check_name(self, name: str) -> bool:
        """
        Проверка допустимости имени хоста

        Parameters
        ----------
        name : str
            Имя хоста.

        Returns
        -------
        bool
            True, если имя хоста допустимо, если же нет, то False.

        """
        if not self.check_len(name):
            return self.ADDRESS_INCORRECT
        if not re.match(self.DOMAIN_RE, name):
            return self.ADDRESS_INCORRECT
        for h in self.restricted_hostnames:
            if name == h:
                return self.ADDRESS_DENIED
        return self.ADDRESS_OK

    def check_ip(self, ip_str: str) -> int:
        logger = logging.getLogger(__name__)
        try:
            ip = ipaddress.ip_address(ip_str)
            if ip.version == 4:
                net_list = self.restricted_ipv4
            elif ip.version == 6:
                net_list = self.restricted_ipv6
            else:
                logger.error("Unknown address type for %s", ip_str)
                return self.ADDRESS_INCORRECT
        except ValueError:
            logger.error("Incorrect address: %s", ip_str)
            return self.ADDRESS_INCORRECT
        for net in net_list:
            if ip in net:
                logger.debug("IP %s in restricted net %s",
                             ip_str,
                             str(net))
                return self.ADDRESS_DENIED
        return self.ADDRESS_OK

    def check_host(self, addr: str) -> bool:
        """
        Проверка адреса хоста (может быть доменное имя или IP-адрес)

        Parameters
        ----------
        addr : str
            Имя или адрес IPv4 или IPv6.

        Returns
        -------
        bool
            True, если адрес допустим (корректен и не запрещён), иначе False.

        """
        if self.IP4_RE.match(addr) or self.IP6_RE.match(addr):
            return self.check_ip(addr)
        else:
            return self.check_name(addr)
