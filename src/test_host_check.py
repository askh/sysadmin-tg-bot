#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 17 21:50:17 2024

@author: askh
"""

import unittest
from host_check import HostChecker

class HostCheckerTest(unittest.TestCase):

    def test_create(self):
        hostname_min_len = 2
        hostname_max_len = 1000
        host_checker = HostChecker(hostname_min_len=hostname_min_len,
                                   hostname_max_len=hostname_max_len)
        self.assertEqual(host_checker.hostname_min_len, hostname_min_len)
        self.assertEqual(host_checker.hostname_max_len, hostname_max_len)
