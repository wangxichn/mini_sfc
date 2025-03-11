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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from minisfc.mano.vim import NfvVim

class VnfManager:
    def __init__(self,vnfParamDict:dict[int:dict[str]]=None):
        """_summary_

        Args:
            vnfParamDict (dict[int:dict[str]]): {id:{paramtype:value}}
        """
        self.vnfPoolDict = vnfParamDict

    def ready(self, nfvVim:'NfvVim'):
        self.nfvVim = nfvVim

    def add_vnf_into_pool(self,vnfParamDict:dict[int:dict[str]]):
        pass

    def get_vnf_from_pool(self,vnfId:int):
        vnfEm = VnfEm(name=f'sfc_*_vnf_*',vnfId=vnfId,vnfParamDict=self.vnfPoolDict[vnfId])
        return vnfEm
        
        
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
        self.cpu_req:float = vnfParamDict.get('cpu',0)
        self.ram_req:float = vnfParamDict.get('ram',0)
        self.rom_req:float = vnfParamDict.get('rom',0)
        self.type:str = vnfParamDict.get('type',None)
        self.img:str = vnfParamDict.get('img',None)

        self.service_bw_map:dict[int:float] = {}


