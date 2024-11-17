#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 16 19:19:49 2024

@author: askh
"""

import copy
import ipaddress


DEFAULT_HOSTNAME_MIN_LEN = 1
DEFAULT_HOSTNAME_MAX_LEN = 1024


class HostChecker:

    def __init__(self,
                 hostname_min_len=DEFAULT_HOSTNAME_MIN_LEN,
                 hostname_max_len=DEFAULT_HOSTNAME_MAX_LEN,
                 restricted_hostnames=[],
                 restricted_ipv4=[],
                 restricted_ipv6=[]):
        self.hostname_min_len = hostname_min_len
        self.hostname_max_len = hostname_max_len
        self.restricted_hostnames = copy.copy(restricted_hostnames)
        self.restricted_ipv4 = copy.copy(restricted_ipv4)
        self.restricted_ipv6 = copy.copy(restricted_ipv6)

    def ok(self, host: str) -> bool:
        return self.is_correct(host) and self.is_allowed(self)

    def check_len(self, host: str) -> bool:
        return len(host) <= self.hostname_max_len

