#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 01:45:14 2024

@author: askh
"""

import unittest

# from sysadmin_tg_bot import DOMAIN_NAME_MAX_LENGTH, \
    # check_host_name, data_to_str, \
    # check_site_url

from sysadmin_tg_bot import data_to_str, check_site_url

class GeneralTest(unittest.TestCase):


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
