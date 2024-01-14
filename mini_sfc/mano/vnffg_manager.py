#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   vnffg_manager.py
@Time    :   2024/01/14 21:36:07
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from data import ServiceChain

class VnffgManager:
    def __init__(self,service_chain:ServiceChain) -> None:
        self.service_chain = service_chain


