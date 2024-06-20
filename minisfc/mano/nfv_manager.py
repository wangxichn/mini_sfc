#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   nfv_manager.py
@Time    :   2024/06/18 15:15:00
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

class NfvManager:
    def __init__(self,vnfParamDict:dict[int:dict[str]]):
        """_summary_

        Args:
            vnfParamDict (dict[int:dict[str]]): {id:{paramtype:value}}
        """
        self.vnfPoolDict = vnfParamDict
        
        

