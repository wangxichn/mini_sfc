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
import copy
import code

class NfvOrchestrator:
    def __init__(self,**kwargs) -> None:
        self.setting = kwargs
        self.solver_name = self.setting.get("solver_name","baseline_random")
        self.vnffg_manager_setting = {"solver_name":self.solver_name}

    def ready(self,substrate_network:SubstrateNetwork):
        self.substrate_network = substrate_network
        self.vnffg_group:list[VnffgManager] = []

    def handle(self,event:Event):
        if event.type == EventType.SFC_ARRIVE:
            vnffg_manager = VnffgManager(event.sfc,
                                         copy.deepcopy(self.substrate_network),
                                         **self.vnffg_manager_setting)

            self.substrate_network, _ = vnffg_manager.handle_arrive() # solution to do------------------------
            self.vnffg_group.append(vnffg_manager)
            
        elif event.type == EventType.SFC_ENDING:
            vnffg_manager = list(filter(lambda x: x.service_chain.id == event.sfc_id, self.vnffg_group))
            if vnffg_manager != []:
                vnffg_manager = vnffg_manager[0]
                self.substrate_network, _ = vnffg_manager.handle_ending() # solution to do--------------------
                self.vnffg_group = list(filter(lambda x: x.service_chain.id != id, self.vnffg_group))

        elif event.type == EventType.TOPO_CHANGE:
            # fine the vnffg_manager will be affected to do---------------------------------------------------
            pass





