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
import copy

if TYPE_CHECKING:
    from minisfc.mano.vim import NfvVim

class VnfManager:
    def __init__(self):
        """_summary_

        Args:
            vnfParamDict (dict[int:dict[str]]): {id:{paramtype:value}}
        """
        self.vnfPoolDict:dict[int:VnfEm] = {}
        self.vnfServicePoolDict:dict[tuple:dict[str:float]] = {}

    def ready(self, nfvVim:'NfvVim'):
        self.nfvVim = nfvVim

    def add_vnf_into_pool(self,vnfEm_template:'VnfEm'):
        vnfId = vnfEm_template.vnfId
        if vnfId in self.vnfPoolDict:
            raise ValueError(f'VNF ID {vnfId} already exists in VNF pool')
        else:
            self.vnfPoolDict[vnfId] = vnfEm_template
    
    def add_vnf_service_into_pool(self,vnfId_1:int,vnfId_2:int,**kwargs):
        if vnfId_1 not in self.vnfPoolDict or vnfId_2 not in self.vnfPoolDict:
            raise ValueError(f'VNF ID {vnfId_1} or {vnfId_2} does not exist in VNF pool')
        elif (vnfId_1,vnfId_2) in self.vnfServicePoolDict:
            raise ValueError(f'Service between VNF {vnfId_1} and VNF {vnfId_2} already exists in VNF service pool')
        else:
            self.vnfServicePoolDict[(vnfId_1,vnfId_2)] = kwargs

    def get_vnf_from_pool(self,vnfId:int) -> 'VnfEm':
        if vnfId not in self.vnfPoolDict:
            raise ValueError(f'VNF ID {vnfId} does not exist in VNF pool')
        vnfEm = copy.deepcopy(self.vnfPoolDict[vnfId])
        return vnfEm
        
        
class VnfEm:
    def __init__(self,**kwargs):
        """VNF Element Management

        Args:
            name (str): _description_
            vnfId (int): _description_
            vnfParamDict (_type_): _description_
        """
        self.kwargs = kwargs

        self.name:str = kwargs.get('name',f'sfc_*_vnf_*')
        self.vnfId = kwargs.get('vnfId',None)
        self.cpu_req:float = kwargs.get('cpu',0)
        self.ram_req:float = kwargs.get('ram',0)
        self.rom_req:float = kwargs.get('rom',0)

        self.container_vnf_handle = kwargs.get('container_vnf_handle',None)
        self.type:str = kwargs.get('type',None)
        self.img:str = kwargs.get('img',None)
        self.ip:str = kwargs.get('ip',None)
        self.port:int = kwargs.get('port',None)
        self.cmd:str = kwargs.get('cmd',None)

    def update_vnf_param(self,**kwargs):
        self.kwargs.update(kwargs)

        self.name = self.kwargs.get('name',self.name)
        self.vnfId = self.kwargs.get('vnfId',self.vnfId)
        self.cpu_req:float = self.kwargs.get('cpu',self.cpu_req)
        self.ram_req:float = self.kwargs.get('ram',self.ram_req)
        self.rom_req:float = self.kwargs.get('rom',self.rom_req)

        self.container_vnf_handle = self.kwargs.get('container_vnf_handle',self.container_vnf_handle)
        self.type:str = self.kwargs.get('type',self.type)
        self.img:str = self.kwargs.get('img',self.img)
        self.ip:str = self.kwargs.get('ip',self.ip)
        self.port:int = self.kwargs.get('port',self.port)
        self.cmd:str = self.kwargs.get('cmd',self.cmd)