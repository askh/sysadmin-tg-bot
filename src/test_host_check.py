#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 17 21:50:17 2024

@author: askh
"""

import unittest
from host_check import HostChecker


class HostCheckerTest(unittest.TestCase):

    def setUp(self):
        self.host_checker = HostChecker(hostname_min_len=2,
                                        hostname_max_len=100,
                                        restricted_hostnames=['localhost'],
                                        restricted_ipv4=['127.0.0.0/8'],
                                        restricted_ipv6=['::1/128'])

    def test_create(self):
        hostname_min_len = 2
        hostname_max_len = 1000
        host_checker = HostChecker(hostname_min_len=hostname_min_len,
                                   hostname_max_len=hostname_max_len)
        self.assertEqual(host_checker.hostname_min_len, hostname_min_len)
        self.assertEqual(host_checker.hostname_max_len, hostname_max_len)

    def test_check_host_too_short(self):
        too_short = ''
        self.assertEqual(self.host_checker.check_host(too_short),
                         self.host_checker.ADDRESS_INCORRECT)

    def test_check_host_too_big(self):
        too_big = 'x' * self.host_checker.hostname_max_len + '.ru'
        self.assertEqual(self.host_checker.check_host(too_big),
                         self.host_checker.ADDRESS_INCORRECT)

    def test_check_host_normal_max_len(self):
        normal = 'x' * (self.host_checker.hostname_max_len - 3) + '.ru'
        self.assertEqual(self.host_checker.check_host(normal),
                         self.host_checker.ADDRESS_OK)

    def test_check_host_normal_chars(self):
        for name in ('example.com', 'example.ru', 'пример.рф', 'аяё.рф',
                     'test123.com', 'пример1.рф',
                     '1.2.3.4'):
            self.assertEqual(
                self.host_checker.check_host(name),
                self.host_checker.ADDRESS_OK,
                msg=f"Problem for name {name}")

    def test_check_host_illegal_chars(self):
        for host in ('example.com', 'пример.рф', '1.2.3.4'):
            for char in (' ', '\t', '\n', '\r'):
                for name in (f"{char}{host}",
                             f"{host}{char}",
                             f"{char}{host}{char}"):
                    self.assertEqual(
                        self.host_checker.check_host(name),
                        self.host_checker.ADDRESS_INCORRECT,
                        msg=f"Problem for name {name}")
        for name in ("\t\n", ':.ru'):
            self.assertEqual(
                self.host_checker.check_host(name),
                self.host_checker.ADDRESS_INCORRECT,
                msg=f"Problem for name {name}")

    def test_restricted_hosts(self):
        for addr in ('localhost', '127.0.0.1', '127.1.0.1', '::1'):
            self.assertEqual(
                self.host_checker.check_host(addr),
                self.host_checker.ADDRESS_DENIED)
