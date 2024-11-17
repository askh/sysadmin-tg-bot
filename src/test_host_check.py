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
                                        hostname_max_len=100)

    def test_create(self):
        hostname_min_len = 2
        hostname_max_len = 1000
        host_checker = HostChecker(hostname_min_len=hostname_min_len,
                                   hostname_max_len=hostname_max_len)
        self.assertEqual(host_checker.hostname_min_len, hostname_min_len)
        self.assertEqual(host_checker.hostname_max_len, hostname_max_len)

    def test_check_host_name_too_short(self):
        too_short = ''
        self.assertFalse(self.host_checker.check_host_name(too_short))

    def test_check_host_name_too_big(self):
        too_big = 'x' * self.host_checker.hostname_max_len + '.ru'
        self.assertFalse(self.host_checker.check_host_name(too_big))

    def test_check_host_name_normal_max_len(self):
        normal = 'x' * (self.host_checker.hostname_max_len - 3) + '.ru'
        self.assertTrue(self.host_checker.check_host_name(normal))

    def test_check_host_name_normal_chars(self):
        for name in ('example.com', 'example.ru', 'пример.рф', 'аяё.рф',
                     'test123.com', 'пример1.рф',
                     '1.2.3.4'):
            self.assertTrue(
                self.host_checker.check_host_name(name),
                msg=f"Problem for name {name}")

    def test_check_host_name_illegal_chars(self):
        for host in ('example.com', 'пример.рф', '1.2.3.4'):
            for char in (' ', '\t', '\n', '\r'):
                for name in (f"{char}{host}",
                             f"{host}{char}",
                             f"{char}{host}{char}"):
                    self.assertFalse(
                        self.host_checker.check_host_name(name),
                        msg=f"Problem for name {name}")
        for name in ("\t\n", ':.ru'):
            self.assertFalse(
                self.host_checker.check_host_name(name),
                msg=f"Problem for name {name}")
