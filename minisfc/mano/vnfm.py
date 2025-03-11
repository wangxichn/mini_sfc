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

class VnfManager:
    def __init__(self,vnfParamDict:dict[int:dict[str]]=None):
        """_summary_

        Args:
            vnfParamDict (dict[int:dict[str]]): {id:{paramtype:value}}
        """
        self.vnfPoolDict = vnfParamDict

    def init_vnf_pool(self,vnfParamDict:dict[int:dict[str]]):
        self.vnfPoolDict = vnfParamDict
        
        
class VnfEm:
    def __init__(self,name:str,vnfId:int,vnfParamDict:dict[str:str]):
        """VNF Element Management

        Args:
            name (str): _description_
            vnfId (int): _description_
            vnfParamDict (_type_): _description_
        """
        self.name = name
        self.vnfId = vnfId
        self.cpu = vnfParamDict.get('cpu',None)
        self.ram = vnfParamDict.get('ram',None)
        self.rom = vnfParamDict.get('rom',None)
        self.type = vnfParamDict.get('type',None)
        self.img = vnfParamDict.get('img',None)


