#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 16 19:19:49 2024

@author: askh
"""

import copy
import ipaddress
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
        self.hostname_min_len = \
            self._change_none(hostname_min_len,
                              self.DEFAULT_HOSTNAME_MIN_LEN)
        self.hostname_max_len = \
            self._change_none(hostname_max_len,
                              self.DEFAULT_HOSTNAME_MAX_LEN)
        self.restricted_hostnames = copy.copy(restricted_hostnames)
        self.restricted_ipv4 = copy.copy(restricted_ipv4)
        self.restricted_ipv6 = copy.copy(restricted_ipv6)

    def ok(self, host: str) -> bool:
        return self.is_correct(host) and self.is_allowed(self)

    def check_len(self, host: str) -> bool:
        return len(host) <= self.hostname_max_len

    def check_host_name(self, name: str) -> bool:
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
        name_len = len(name)
        if name_len < self.hostname_min_len or \
           name_len > self.hostname_max_len:
            return False
        if not re.match(self.DOMAIN_RE, name):
            return False
        return True
