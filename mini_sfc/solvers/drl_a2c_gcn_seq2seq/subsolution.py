#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   subsolution.py
@Time    :   2024/03/27 19:12:03
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''


class SubSolution():
    def __init__(self) -> None:
        self.try_times = 0

        self.selected_actions = []

        self.result = False
        self.place_result = False
        self.route_result = False
        self.rejection = False

        self.reward = 0




