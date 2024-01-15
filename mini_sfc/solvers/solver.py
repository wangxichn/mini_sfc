#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   solver.py
@Time    :   2024/01/15 14:54:25
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

import inspect
from solvers import Solution

class SolverRegistrar:
    def __init__(self) -> None:
        self._solver_dict = {}

    def get(self, solver_name: str) -> object:
        solver_name = solver_name.lower()
        if solver_name not in self._solver_dict.keys():
            raise KeyError(f'The solver {solver_name} is not in the registry')
        return self._solver_dict.get(solver_name)

    def __add(self, solver_name: str, solver_cls: object) -> None:
        if not inspect.isclass(solver_cls):
            raise TypeError(f'module must be a class, but got {type(solver_cls)}')
        if solver_name in self._solver_dict:
            raise KeyError(f'{solver_name} is already registered')
        self._solver_dict[solver_name.lower()] = solver_cls

    def regist(self, solver_name: str) -> object:
        def _regist(solver_cls):
            solver_cls.name = solver_name
            self.__add(solver_name, solver_cls)
            return solver_cls
        return _regist

SOLVER_REGISTRAR = SolverRegistrar()

class Solver:
    def __init__(self) -> None:
        pass

    def solve() -> Solution:
        return NotImplementedError
