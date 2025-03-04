#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   nfv_vim.py
@Time    :   2024/01/14 21:37:19
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from data import SubstrateNetwork

class NfvVim:
    def __init__(self,**kwargs) -> None:
        self.attrs = kwargs
