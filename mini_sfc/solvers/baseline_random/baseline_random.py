#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   baseline_random.py
@Time    :   2024/01/15 15:07:59
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from solvers import SOLVER_REGISTRAR
from solvers import Solver
from solvers import Solution

@SOLVER_REGISTRAR.regist(solver_name='baseline_random')
class BaselineRandom(Solver):
    def __init__(self) -> None:
        super().__init__()

    def initialize(self):
        self.solution = Solution()
        
    def solve():
        pass
        

