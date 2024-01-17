#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   baseline_random.py
@Time    :   2024/01/15 15:07:59
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from solvers import Solution
from solvers import SOLVER_REGISTRAR
from solvers import Solver
from solvers import Solution, SOLUTION_TYPE
from base import Event,EventType
import networkx as nx
import random
import code
import copy 
import time
import numpy as np

@SOLVER_REGISTRAR.regist(solver_name='baseline_random')
class BaselineRandom(Solver):
    def __init__(self) -> None:
        super().__init__()

    def initialize(self,event: Event) -> None:
        self.solution = Solution()
        self.service_chain = event.sfc
        self.substrate_network = event.current_substrate

        MAX_CPU_Y = max(self.substrate_network.get_all_nodes_attrs_values("cpu_setting","max_setting"))+1
        MAX_RAM_X = max(self.substrate_network.get_all_nodes_attrs_values("ram_setting","max_setting"))+1
        MIN_DEVISE_LATENCY = 0.01
        MAX_DEVISE_LATENCY = MIN_DEVISE_LATENCY + MIN_DEVISE_LATENCY * (MAX_CPU_Y-1+MAX_RAM_X-1)
        self.DEVISE_LATENCY_MAT = np.zeros((MAX_CPU_Y,MAX_RAM_X))
        for i in range(MAX_CPU_Y):
            for j in range(MAX_RAM_X):
                self.DEVISE_LATENCY_MAT[i,j] = MAX_DEVISE_LATENCY-(i+j)*MIN_DEVISE_LATENCY

    def solve_embedding(self,event: Event) -> Solution:
        self.service_chain = event.sfc
        self.substrate_network = event.current_substrate

        self.solution.current_time = event.time
        self.solution.current_service_chain = event.sfc
        self.solution.current_substrate_net = copy.deepcopy(event.current_substrate)

        solve_start_time = time.time()

        # algorithm begin ---------------------------------------------
        
        for v_node in self.service_chain.nodes:
            self.solution.map_node[v_node] = random.sample(range(self.substrate_network.num_nodes),1)[0]

        for v_link in self.service_chain.edges():
            map_path = nx.dijkstra_path(self.substrate_network,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        
        
        self.solution.current_description = self.__check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.SET_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True

        self.__perform_measure(event)
        self.solution.cost_real_time = time.time()-solve_start_time

        return self.solution
    
    def solve_migration(self,event: Event) -> Solution:
        self.service_chain = event.sfc
        self.substrate_network = event.current_substrate

        self.solution.current_time = event.time
        self.solution.current_service_chain = event.sfc
        self.solution.current_substrate_net = copy.deepcopy(event.current_substrate)

        solve_start_time = time.time()

        # algorithm begin ---------------------------------------------
        
        for v_node in self.service_chain.nodes:
            self.solution.map_node[v_node] = random.sample(range(self.substrate_network.num_nodes),1)[0]

        for v_link in self.service_chain.edges():
            map_path = nx.dijkstra_path(self.substrate_network,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]

        self.solution.current_description = SOLUTION_TYPE.CHANGE_SUCCESS
        self.solution.current_result = True

        self.__perform_measure(event)
        
        # algorithm end ----------------------------------------------
                
        solve_end_time = time.time()

        self.solution.cost_real_time = solve_end_time-solve_start_time

        return self.solution

    def solve_ending(self,event: Event) -> Solution:
        self.service_chain = event.sfc
        self.substrate_network = event.current_substrate

        self.solution.current_time = event.time
        self.solution.current_service_chain = event.sfc
        self.solution.current_substrate_net = copy.deepcopy(event.current_substrate)

        solve_start_time = time.time()

        # algorithm begin ---------------------------------------------
        
        self.solution.map_node = self.solution.map_node # Get previous data 
        self.solution.map_link = self.solution.map_link # Get previous data 

        self.solution.current_description = SOLUTION_TYPE.END_SUCCESS
        self.solution.current_result = True

        self.__perform_measure(event)

        # algorithm end ----------------------------------------------
                
        solve_end_time = time.time()

        self.solution.cost_real_time = solve_end_time-solve_start_time

        return self.solution

    def __check_constraints(self, event: Event) -> SOLUTION_TYPE:
        # Node Resource Constraint Check
        for sfc_node, phy_node in self.solution.map_node.items():
            remain_cpu_of_node = self.substrate_network.get_node_attrs_value(phy_node,"cpu_setting","remain_setting")
            request_cpu_of_node = self.service_chain.get_node_attrs_value(sfc_node,"cpu_setting")
            remain_ram_of_node = self.substrate_network.get_node_attrs_value(phy_node,"ram_setting","remain_setting")
            request_ram_of_node = self.service_chain.get_node_attrs_value(sfc_node,"ram_setting")
            remain_disk_of_node = self.substrate_network.get_node_attrs_value(phy_node,"disk_setting","remain_setting")
            request_disk_of_node = self.service_chain.get_node_attrs_value(sfc_node,"disk_setting")
            remain_eng_of_node = self.substrate_network.get_node_attrs_value(phy_node,"energy_setting","remain_setting")
            request_eng_of_node = request_cpu_of_node * (self.service_chain.endtime - self.solution.current_time)

            if True in (request_cpu_of_node > remain_cpu_of_node, request_ram_of_node > remain_ram_of_node,
                        request_disk_of_node > remain_disk_of_node, request_eng_of_node > remain_eng_of_node):
                if event.type == EventType.SFC_ARRIVE:
                    return SOLUTION_TYPE.SET_NODE_FAILED
                elif event.type == EventType.TOPO_CHANGE:
                    return SOLUTION_TYPE.CHANGE_NODE_FAILED
            
        # Link Resource Constraint Check
        CHECK_FLAG = True
        for sfc_link, phy_links in self.solution.map_link.items():
            if CHECK_FLAG == False: break
            request_band_of_link = self.service_chain.get_link_attrs_value(sfc_link,"band_setting")
            for phy_link in phy_links:
                remain_band_of_link = self.substrate_network.get_link_attrs_value(phy_link,"band_setting","remain_setting")
                if request_band_of_link > remain_band_of_link:
                    CHECK_FLAG = False
                    break
        if CHECK_FLAG == False:
            if event.type == EventType.SFC_ARRIVE:
                return SOLUTION_TYPE.SET_LINK_FAILED
            elif event.type == EventType.TOPO_CHANGE:
                return SOLUTION_TYPE.CHANGE_LINK_FAILED
        
        # Qos Constraint Check
        latency = self.__get_latency_running()
        if latency > event.sfc.qos_latency:
            if event.type == EventType.SFC_ARRIVE:
                return SOLUTION_TYPE.SET_LATENCY_FAILED
            elif event.type == EventType.TOPO_CHANGE:
                return SOLUTION_TYPE.CHANGE_LATENCY_FAILED
        
        # All check passed
        return SOLUTION_TYPE.SET_SUCCESS

    def __perform_measure(self,event: Event):

        perform_all_use_cpu_resource = sum(self.service_chain.get_all_nodes_attrs_values("cpu_setting"))
        perform_all_use_ram_resource = sum(self.service_chain.get_all_nodes_attrs_values("ram_setting"))
        perform_all_use_disk_resource = sum(self.service_chain.get_all_nodes_attrs_values("disk_setting"))
        perform_all_use_energy_resource = sum(self.service_chain.get_all_nodes_attrs_values("cpu_setting"))

        perform_all_use_link_resource = 0
        for sfd_link, phy_links in self.solution.map_link.items():
            perform_all_use_link_resource += self.service_chain.get_link_attrs_value(sfd_link,"band_setting") * len(phy_links)

        perform_all_phy_cpu_resource = sum(self.substrate_network.get_all_nodes_attrs_values("cpu_setting","max_setting"))
        perform_all_phy_ram_resource = sum(self.substrate_network.get_all_nodes_attrs_values("ram_setting","max_setting"))
        perform_all_phy_disk_resource = sum(self.substrate_network.get_all_nodes_attrs_values("disk_setting","max_setting"))
        perform_all_phy_energy_resource = sum(self.substrate_network.get_all_nodes_attrs_values("cpu_setting","max_setting"))
        perform_all_phy_link_resource = sum(self.substrate_network.get_all_links_attrs_values("band_setting","max_setting"))

        perform_revenue = (perform_all_use_cpu_resource * self.substrate_network.get_node_attrs_price("cpu_setting") + \
                           perform_all_use_ram_resource * self.substrate_network.get_node_attrs_price("ram_setting") + \
                           perform_all_use_disk_resource * self.substrate_network.get_node_attrs_price("disk_setting") + \
                           perform_all_use_energy_resource * self.substrate_network.get_node_attrs_price("energy_setting") + \
                           perform_all_use_link_resource * self.substrate_network.get_link_attrs_price("band_setting")) \
                           * (event.time-event.sfc.arrivetime)

        self.solution.perform_revenue = perform_revenue

        self.solution.perform_latency = self.__get_latency_running()

        self.solution.cost_node_resource = [perform_all_use_cpu_resource, perform_all_use_ram_resource, 
                                            perform_all_use_disk_resource, perform_all_use_energy_resource]
        self.solution.cost_node_resource_percentage = [perform_all_use_cpu_resource/perform_all_phy_cpu_resource, 
                                                       perform_all_use_ram_resource/perform_all_phy_ram_resource, 
                                                       perform_all_use_disk_resource/perform_all_phy_disk_resource, 
                                                       perform_all_use_energy_resource/perform_all_phy_energy_resource]
        self.solution.cost_link_resource = [perform_all_use_link_resource]
        self.solution.cost_link_resource_percentage = [perform_all_use_link_resource/perform_all_phy_link_resource]

    def __get_latency_running(self) -> float:
        latency_list = []
        for phy_node in self.solution.map_node.values():
            latency_list.append(self.substrate_network.get_node_latency_from_mat(phy_node,self.DEVISE_LATENCY_MAT))

        return max(latency_list)


