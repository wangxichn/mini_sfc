#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   nfv_orchestrator.py
@Time    :   2024/01/14 21:38:07
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from data import SubstrateNetwork
from data import ServiceChain
from base import EventType,Event
from mano import VnffgManager
import code

class NfvOrchestrator:
    def __init__(self,**kwargs) -> None:
        self.solver_name = kwargs.get("solver_name","Random")

    def ready(self,substrate_network:SubstrateNetwork):
        self.substrate_network = substrate_network
        self.vnffg_group:list[VnffgManager] = []

    def handle(self,event:Event):
        if event.type == EventType.SFC_ARRIVE:
            vnffg_manager = VnffgManager(event.sfc)
            self.vnffg_group.append(vnffg_manager)
            
        elif event.type == EventType.SFC_ENDING:
            self.__remove_vnffg_with_sfc_id(event.sfc_id)

        elif event.type == EventType.TOPO_CHANGE:
            pass

    def __remove_vnffg_with_sfc_id(self,id:int):
        self.vnffg_group = list(filter(lambda x: x.service_chain.id != id, self.vnffg_group))



