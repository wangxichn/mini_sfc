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

    def handle(self,event:Event) -> SubstrateNetwork:
        if event.type == EventType.SFC_ARRIVE:
            return self.__handle_arrive(event)
        elif event.type == EventType.SFC_ENDING:
            return self.__handle_ending(event)
        elif event.type == EventType.TOPO_CHANGE:
            return self.__handle_topochange(event)

    def __handle_arrive(self,event:Event) -> SubstrateNetwork:
        # Update network state before solve
        self.substrate_network = event.current_substrate
        # Create SFC manager
        vnffg_manager = VnffgManager(event,**self.vnffg_manager_setting)
        # Update network state after solve
        self.substrate_network, solution_group = vnffg_manager.handle_arrive(event)
        # Save SFC manager
        self.vnffg_group.append(vnffg_manager)
        self.vnffg_group_log[vnffg_manager.id] = solution_group

        return self.substrate_network


    def __handle_ending(self,event:Event) -> SubstrateNetwork:
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

        return self.substrate_network

    def __handle_topochange(self,event:Event) -> SubstrateNetwork:
        # update network state
        self.substrate_network = event.current_substrate
        # find the vnffg_manager will be affected to do---------------------------------------------------
        for vnffg_manager in self.vnffg_group:
            # Combine all the mapped physical links in the solution into a list using the sum function
            # And then use set to deduplicate, because we don't care about the order of these links
            all_used_phy_edge = list(set(sum(vnffg_manager.solution_group[-1].map_link.values(),[])))
            current_phy_net_adjacency = self.substrate_network.get_adjacency_matrix()
            for edge in all_used_phy_edge:
                if current_phy_net_adjacency[edge[0],edge[1]] == 0:
                    # Topological changes affect this SFC and require migration
                    # The event is originally a topology change type and does not contain SFC information. It needs to be supplemented here. 
                    event.sfc = vnffg_manager.service_chain
                    self.substrate_network, solution_group = vnffg_manager.handle_topochange(event)
                    self.vnffg_group_log[vnffg_manager.id] = solution_group
                    # After processing this SFC migration, need to update the current substrate network state in the event 
                    event.current_substrate = self.substrate_network
                    break # check next vnffg_manager

        return self.substrate_network
