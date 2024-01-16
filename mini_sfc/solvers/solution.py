#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   solution.py
@Time    :   2024/01/15 14:56:10
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''


class Solution:
    def __init__(self) -> None:
        pass

class SolutionGroup(list[Solution]):
    def __init_subclass__(cls) -> None:
        return super().__init_subclass__()
    
    def append(self, __object: Solution) -> None:
        return super().append(__object)