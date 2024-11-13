#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 12 16:23:00 2024

@author: askh

Содержит класс для ограничения количества запросов по времени
"""


import asyncio
from dataclasses import dataclass
import sys
from time import time
from typing import Any


class RequestLimit:

    @dataclass
    class Request:
        id: Any
        req_time_sec: float

    def __init__(self,
                 max_value: int,
                 max_id_value: int,
                 time_interval_sec: int = 60):
        self.max_value = max_value
        self.max_id_value = max_id_value
        self.time_interval_sec = time_interval_sec
        self.lock = asyncio.Lock()
        self.total_count = 0
        self.id_count: dict[Any] = {}
        self.requests: list[RequestLimit.Request] = []
        self.lock = asyncio.Lock()

    def __purge(self, current_time_sec: float):
        """
        Очистить данные о запросах за пределами отслеживаемого периода.

        Parameters
        ----------
        current_time_sec : float
            Текущее время, в секундах.

        Returns
        -------
        None.

        """
        self.requests = sorted(self.requests, key=lambda x: x.req_time_sec)
        old_time_sec = current_time_sec - self.time_interval_sec
        while self.requests:
            if self.requests[0].req_time_sec <= old_time_sec:
                src_id = self.requests[0].id
                self.total_count -= 1
                self.id_count[src_id] -= 1
                if self.id_count[src_id] == 0:
                    del self.id_count[src_id]
                self.requests.pop(0)
            else:
                break

    async def request(self, src_id: Any, req_time_sec: float = None) -> bool:
        """
        Проверить возможность добавить запрос и зарегистрировать его в
        случае успеха.

        Parameters
        ----------
        id : Any
            Идентификатор инициатора запроса (например, пользователя).
        req_time_sec : float, optional
            Момент поступления запроса, в секундах. The default is None.

        Returns
        -------
        bool
            Возвращает True если запрос можно выполнять (лимит не достигнут)
            и False в противном случае.

        """
        async with self.lock:
            if req_time_sec is None:
                req_time_sec = time()
            self.__purge(req_time_sec)
            if self.total_count >= self.max_value:
                return False
            if self.max_id_value == 0:
                return False
            if src_id in self.id_count and \
               self.id_count[src_id] >= self.max_id_value:
                return False
            self.requests.append(
                RequestLimit.Request(id=src_id,
                                     req_time_sec=req_time_sec))
            self.total_count += 1
            if src_id not in self.id_count:
                self.id_count[src_id] = 1
            else:
                self.id_count[src_id] += 1
        return True
