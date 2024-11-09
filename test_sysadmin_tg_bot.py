#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 01:45:14 2024

@author: askh
"""

import unittest

from sysadmin_tg_bot import DOMAIN_NAME_MAX_LENGTH, \
    check_host_name, data_to_str


class GeneralTest(unittest.TestCase):

    def test_check_host_name_too_big(self):
        too_big = 'x' * DOMAIN_NAME_MAX_LENGTH + '.ru'
        self.assertEqual(check_host_name(too_big), False)

    def test_check_host_name_normal_max_len(self):
        normal = 'x' * (DOMAIN_NAME_MAX_LENGTH - 3) + '.ru'
        self.assertEqual(check_host_name(normal), True)

    def test_check_host_name_normal_chars(self):
        for name in ('example.com', 'example.ru', 'пример.рф'):
            self.assertEqual(check_host_name(name), True)

    def test_check_host_name_illegal_chars(self):
        for name in (' example.com', 'example.com ', ' example.com ',
                     'example com', "\nexample.com", "example.com\n",
                     '\texample.com', 'example.com\t',
                     ' пример.рф', 'пример.рф ',
                     "\t\n"):
            self.assertEqual(check_host_name(name), False)

    def test_data_to_str(self):
        self.assertEqual(data_to_str(''), '')
        self.assertEqual(data_to_str('test'), 'test')
        self.assertEqual(data_to_str(['test']), 'test')
        self.assertEqual(data_to_str(['a', 'b']), 'a, b')
        self.assertEqual(data_to_str(['a', 'b', 'c']), 'a, b, c')
