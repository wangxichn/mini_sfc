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
from typing import Tuple
from solvers import SolutionGroup
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
        self.vnffg_group_log:dict[int,SolutionGroup] = {}

    def handle(self,event:Event) -> Tuple[SubstrateNetwork,dict[int,SolutionGroup]]:
        if event.type == EventType.SFC_ARRIVE:
            # Update network state before solve
            self.substrate_network = event.current_substrate
            # Create SFC manager
            vnffg_manager = VnffgManager(event,**self.vnffg_manager_setting)
            # Update network state after solve
            self.substrate_network, solution_group = vnffg_manager.handle_arrive(event)
            # Save SFC manager
            self.vnffg_group.append(vnffg_manager)
            self.vnffg_group_log[vnffg_manager.id] = solution_group

            return self.substrate_network, self.vnffg_group_log
            
        elif event.type == EventType.SFC_ENDING:
            # Update network state before solve
            self.substrate_network = event.current_substrate
            # Find SFC manager related
            vnffg_manager = list(filter(lambda x: x.service_chain.id == event.sfc.id, self.vnffg_group))
            if vnffg_manager != []:
                # SFC ending normally
                vnffg_manager = vnffg_manager[0]
                # Update network state after solve
                self.substrate_network, solution_group = vnffg_manager.handle_ending(event) # solution to do--------------------
                # Remove SFC manager
                self.vnffg_group_log[vnffg_manager.id] = solution_group
                self.vnffg_group = list(filter(lambda x: x.service_chain.id != event.sfc.id, self.vnffg_group))
            else:
                # SFC has been forcibly ended
                pass

            return self.substrate_network, self.vnffg_group_log

        elif event.type == EventType.TOPO_CHANGE:
            # update network state
            self.substrate_network = event.current_substrate
            # find the vnffg_manager will be affected to do---------------------------------------------------
            

            return self.substrate_network, self.vnffg_group_log





