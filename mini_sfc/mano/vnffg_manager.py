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
from data import SubstrateNetwork
from base import Event
from mano import NfvManager
from solvers import SOLVER_REGISTRAR
from solvers import Solution,SolutionGroup
from typing import Tuple
import code
import copy

class VnffgManager:
    def __init__(self, event:Event, **kwargs) -> None:
        self.setting = kwargs
        
        self.id = event.sfc.id

        # Service Function Chain Property
        self.service_chain = event.sfc
        self.vnf_num = event.sfc.num_nodes
        self.vnf_group:list[NfvManager] = [NfvManager(**event.sfc.nodes[i]) for i in event.sfc.nodes]

        # Substrate Network Property
        self.substrate_network = event.current_substrate

        # Solver Property
        self.solver_name = self.setting.get("solver_name","baseline_random")
        self.solver = SOLVER_REGISTRAR.get(self.solver_name)()
        self.solver.initialize_distributed(event)
        self.solution_group = SolutionGroup()


    def handle_arrive(self, event:Event) -> Tuple[SubstrateNetwork,SolutionGroup]:
        # Update substrate network
        self.substrate_network = event.current_substrate
        # Obtain a solution and apply it
        solution:Solution = self.solver.solve_embedding(event)

        if solution.current_result == True:
            # Embedding successful
            self.__action_embedding(solution)
        else:
            # Embedding failed
            pass

        # Save the solution
        self.solution_group.append(copy.deepcopy(solution))

        return self.substrate_network,self.solution_group


    def handle_ending(self, event:Event) -> Tuple[SubstrateNetwork,SolutionGroup]:
        # Update substrate network
        self.substrate_network = event.current_substrate
        # Obtain a solution and apply it
        solution_last:Solution = self.solution_group[-1]
        solution:Solution = self.solver.solve_ending(event,solution_last)
        self.__action_release(solution)
        # Save the solution
        self.solution_group.append(copy.deepcopy(solution))

        return self.substrate_network,self.solution_group


    def handle_topochange(self, event:Event) -> Tuple[SubstrateNetwork,SolutionGroup]:
        # Update substrate network
        self.substrate_network = event.current_substrate
        # Obtain a solution and apply it
        solution_last:Solution = self.solution_group[-1]
        solution:Solution = self.solver.solve_migration(event,solution_last)

        if solution.current_result == True:
            # Migration successful
            self.__action_release(self.solution_group[-1]) # use last one solution release resource
            self.__action_embedding(solution)
        else:
            # Migration failed
            self.__action_release(self.solution_group[-1])

        # Save the solution
        self.solution_group.append(copy.deepcopy(solution))

        return self.substrate_network,self.solution_group


    def __action_embedding(self, solution:Solution):
        # first embed nodes
        for sfc_node, phy_node in solution.map_node.items():
            # CPU
            remain_cpu_of_node = self.substrate_network.get_node_attrs_value(phy_node,"cpu_setting","remain_setting")
            request_cpu_of_node = self.service_chain.get_node_attrs_value(sfc_node,"cpu_setting")
            self.substrate_network.set_node_attrs_value(phy_node,"cpu_setting","remain_setting",remain_cpu_of_node-request_cpu_of_node)

            # RAM
            remain_ram_of_node = self.substrate_network.get_node_attrs_value(phy_node,"ram_setting","remain_setting")
            request_ram_of_node = self.service_chain.get_node_attrs_value(sfc_node,"ram_setting")
            self.substrate_network.set_node_attrs_value(phy_node,"ram_setting","remain_setting",remain_ram_of_node-request_ram_of_node)

            # DISK
            remain_disk_of_node = self.substrate_network.get_node_attrs_value(phy_node,"disk_setting","remain_setting")
            request_disk_of_node = self.service_chain.get_node_attrs_value(sfc_node,"disk_setting")
            self.substrate_network.set_node_attrs_value(phy_node,"disk_setting","remain_setting",remain_disk_of_node-request_disk_of_node)

            # ENG
            remain_eng_of_node = self.substrate_network.get_node_attrs_value(phy_node,"energy_setting","remain_setting")
            request_eng_of_node = request_cpu_of_node * (self.service_chain.endtime - solution.current_time)
            self.substrate_network.set_node_attrs_value(phy_node,"energy_setting","remain_setting",remain_eng_of_node-request_eng_of_node)

        # second embed links
        for sfc_link, phy_links in solution.map_link.items():
            request_band_of_link = self.service_chain.get_link_attrs_value(sfc_link,"band_setting")
            for phy_link in phy_links:
                remain_band_of_link = self.substrate_network.get_link_attrs_value(phy_link,"band_setting","remain_setting")
                self.substrate_network.set_link_attrs_value(phy_link,"band_setting","remain_setting",remain_band_of_link-request_band_of_link)
        
    def __action_release(self, solution:Solution):
        # first release nodes
        for sfc_node, phy_node in solution.map_node.items():
            # CPU
            remain_cpu_of_node = self.substrate_network.get_node_attrs_value(phy_node,"cpu_setting","remain_setting")
            used_cpu_of_node = self.service_chain.get_node_attrs_value(sfc_node,"cpu_setting")
            self.substrate_network.set_node_attrs_value(phy_node,"cpu_setting","remain_setting",remain_cpu_of_node+used_cpu_of_node)

            # RAM
            remain_ram_of_node = self.substrate_network.get_node_attrs_value(phy_node,"ram_setting","remain_setting")
            used_ram_of_node = self.service_chain.get_node_attrs_value(sfc_node,"ram_setting")
            self.substrate_network.set_node_attrs_value(phy_node,"ram_setting","remain_setting",remain_ram_of_node+used_ram_of_node)

            # DISK
            remain_disk_of_node = self.substrate_network.get_node_attrs_value(phy_node,"disk_setting","remain_setting")
            used_disk_of_node = self.service_chain.get_node_attrs_value(sfc_node,"disk_setting")
            self.substrate_network.set_node_attrs_value(phy_node,"disk_setting","remain_setting",remain_disk_of_node+used_disk_of_node)

            # ENG
            remain_eng_of_node = self.substrate_network.get_node_attrs_value(phy_node,"energy_setting","remain_setting")
            unused_eng_of_node = used_cpu_of_node * (self.service_chain.lifetime - (solution.current_time - self.service_chain.arrivetime))
            self.substrate_network.set_node_attrs_value(phy_node,"energy_setting","remain_setting",remain_eng_of_node+unused_eng_of_node)

        # second release links
        for sfc_link, phy_links in solution.map_link.items():
            used_band_of_link = self.service_chain.get_link_attrs_value(sfc_link,"band_setting")
            for phy_link in phy_links:
                try: # the link may have been break
                    remain_band_of_link = self.substrate_network.get_link_attrs_value(phy_link,"band_setting","remain_setting")
                    self.substrate_network.set_link_attrs_value(phy_link,"band_setting","remain_setting",remain_band_of_link+used_band_of_link)
                except:
                    continue

