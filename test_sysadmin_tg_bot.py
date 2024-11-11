#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 01:45:14 2024

@author: askh
"""

import unittest

from sysadmin_tg_bot import DOMAIN_NAME_MAX_LENGTH, \
    check_host_name, data_to_str, \
    check_site_url


class GeneralTest(unittest.TestCase):

    def test_check_host_name_too_short(self):
        too_short = ''
        self.assertFalse(check_host_name(too_short))

    def test_check_host_name_too_big(self):
        too_big = 'x' * DOMAIN_NAME_MAX_LENGTH + '.ru'
        self.assertFalse(check_host_name(too_big))

    def test_check_host_name_normal_max_len(self):
        normal = 'x' * (DOMAIN_NAME_MAX_LENGTH - 3) + '.ru'
        self.assertTrue(check_host_name(normal))

    def test_check_host_name_normal_chars(self):
        for name in ('example.com', 'example.ru', 'пример.рф', 'аяё.рф',
                     'test123.com', 'пример1.рф',
                     '1.2.3.4'):
            self.assertTrue(
                check_host_name(name),
                msg=f"Problem for name {name}")

    def test_check_host_name_illegal_chars(self):
        for host in ('example.com', 'пример.рф', '1.2.3.4'):
            for char in (' ', '\t', '\n', '\r'):
                for name in (f"{char}{host}",
                             f"{host}{char}",
                             f"{char}{host}{char}"):
                    self.assertFalse(
                        check_host_name(name),
                        msg=f"Problem for name {name}")
        for name in ("\t\n", ':.ru'):
            self.assertFalse(
                check_host_name(name),
                msg=f"Problem for name {name}")

    def test_data_to_str(self):
        self.assertEqual(data_to_str(''), '')
        self.assertEqual(data_to_str([]), '')
        self.assertEqual(data_to_str('test'), 'test')
        self.assertEqual(data_to_str(['test']), 'test')
        self.assertEqual(data_to_str(['a', 'b']), 'a, b')
        self.assertEqual(data_to_str(['a', 'b', 'c']), 'a, b, c')

    def test_check_site_url(self):

        # Допустимые варианты

        for host in ('example.ru', 'пример.рф', 'EXAMPLE.RU', 'ПРИМЕР.РФ'):
            for proto in ('https://', 'http://', ''):
                for port in ('', ':80', ':8080'):
                    for path in ('', '/'):
                        url = proto + host + port + path
                        self.assertTrue(check_site_url(url),
                                        msg=f"Problem for url {url}")

        # Недопустимые варианты

        for host in ('example.ru', 'пример.рф', 'EXAMPLE.RU', 'ПРИМЕР.РФ'):
            for path in ('', '/', '/test', '/test.php', '/?test',
                         '/test?test'):
                for proto in ('/', '//', '///', './', 'ftp://',
                              'file:/', 'file://', 'file:///'):
                    url = f"{proto}{host}{path}"
                    self.assertFalse(check_site_url(url),
                                     msg=f"Problem for url {url}")
            for path in ('/test', '/test.php', '/?test', '/test?test'):
                for proto in ('', 'http://', 'https://'):
                    url = f"{proto}{host}{path}"
                    self.assertFalse(check_site_url(url),
                                     msg=f"Problem for url {url}")

        for host in ('example .ru', 'example ru'):
            for proto in ('', 'http://', 'https://'):
                url = f"{proto}{host}"
                self.assertFalse(
                    check_site_url(url),
                    msg=f"Problem for url {url}")
