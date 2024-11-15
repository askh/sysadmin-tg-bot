#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 03:24:43 2024

@author: askh
"""

import unittest
from request_limit import RequestLimit


class RequestLimitTest(unittest.TestCase):

    def test_create(self):
        max_total_value = 6
        max_id_value = 4
        time_interval_sec = 120
        rl = RequestLimit(max_total_value, max_id_value, time_interval_sec)
        self.assertEqual(max_total_value, rl.max_total_value)
        self.assertEqual(max_id_value, rl.max_id_value)
        self.assertEqual(time_interval_sec, rl.time_interval_sec)

    def test_add_request(self):
        max_total_value = 4
        max_id_value = 2
        time_interval_sec = 10
        rl = RequestLimit(max_total_value, max_id_value, time_interval_sec)
        id0 = 100
        id1 = 101
        id2 = 102
        id3 = 103
        id4 = 104
        time0 = 1000.0

        r = rl.request(id0, time0)
        self.assertTrue(r, msg="Start time, id0")

        r = rl.request(id0, time0 + 1)
        self.assertTrue(r, msg="Start time + 1, id0")

        r = rl.request(id0, time0 + 2)
        self.assertFalse(r, msg="Start time + 2, id0")

        r = rl.request(id1, time0 + 2)
        self.assertTrue(r, msg="Start time + 2, id1")

        r = rl.request(id2, time0 + 2)
        self.assertTrue(r, msg="Start time + 2, id2")

        r = rl.request(id1, time0 + 2)
        self.assertFalse(r, msg="Start time + 2, id1")

        r = rl.request(id0, time0 + time_interval_sec)
        self.assertTrue(r, msg="Start time + time interval, id0")

        r = rl.request(id1, time0 + time_interval_sec)
        self.assertFalse(r, msg="Start time + time interval, id1")

        r = rl.request(id1, time0 + time_interval_sec + 2)
        self.assertTrue(r, msg="Start time + time interval + 2, id1")

        r = rl.request(id2, time0 + time_interval_sec + 2)
        self.assertTrue(r, msg="Start time + time interval + 2, id2")

        r = rl.request(id3, time0 + time_interval_sec + 2)
        self.assertTrue(r, msg="Start time + time interval + 2, id3")

        r = rl.request(id4, time0 + time_interval_sec + 2)
        self.assertFalse(r, msg="Start time + time interval + 2, id4")
