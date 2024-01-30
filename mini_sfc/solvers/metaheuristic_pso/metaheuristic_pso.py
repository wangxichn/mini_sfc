#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   metaheuristic_pso.py
@Time    :   2024/01/22 09:47:41
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from solvers import SOLVER_REGISTRAR,Solver
from solvers import Solution, SOLUTION_TYPE, SolutionGroup
from base import Event,EventType
import networkx as nx
import code
import copy 
import time
import numpy as np
import csv
import logging
from sko.PSO import PSO

@SOLVER_REGISTRAR.regist(solver_name='metaheuristic_pso')
class MetaHeuristicPso(Solver):

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
        self.event = event
        self.service_chain = event.sfc
        self.substrate_network = event.current_substrate

        self.solution.current_time = event.time
        self.solution.current_service_chain = copy.deepcopy(event.sfc)
        self.solution.current_substrate_net = copy.deepcopy(event.current_substrate)

        solve_start_time = time.time()

        # algorithm begin ---------------------------------------------
        for v_node in self.service_chain.nodes:
            self.solution.map_node_last[v_node] = None

        for v_link in self.service_chain.edges():
            self.solution.map_link_last[v_link] = []

        pso = PSO(
    	    func=self.calc_fitness, 
    	    dim=self.service_chain.num_nodes*self.substrate_network.num_nodes,
            pop=50, 
    	    max_iter=50, 
    	    lb=[0]*(self.service_chain.num_nodes*self.substrate_network.num_nodes), 
    	    ub=[1]*(self.service_chain.num_nodes*self.substrate_network.num_nodes), 
    	    w=0.8,
    	    c1=0.5, 
    	    c2=0.5)
        pso.run()

        # ################################## PSO iterative observation part begin
        # with open("pso_iteration_data.csv", 'a+', newline='') as csv_file:
        #     csv.writer(csv_file,dialect='excel',delimiter=',').writerow(pso.gbest_y_hist)
        # ################################## PSO iterative observation part end

        x = np.array(pso.gbest_x)
        x = x.reshape((self.service_chain.num_nodes,self.substrate_network.num_nodes))
        for v_node in self.service_chain.nodes:
            self.solution.map_node[v_node] = np.where(x[v_node,:]==np.max(x[v_node,:]))[0][0]

        for v_link in self.service_chain.edges():
            map_path = nx.dijkstra_path(self.substrate_network,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            
            self.solution.map_link_last[v_link] = []
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        
        # algorithm end ---------------------------------------------
        
        self.solution.current_description = self.__check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.SET_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True

        self.__perform_measure(event)
        self.solution.cost_real_time = time.time()-solve_start_time

        return self.solution
    
    def solve_migration(self,event: Event) -> Solution:
        self.event = event
        self.service_chain = event.sfc
        self.substrate_network = event.current_substrate

        self.solution.current_time = event.time
        self.solution.current_service_chain = copy.deepcopy(event.sfc)
        self.solution.current_substrate_net = copy.deepcopy(event.current_substrate)

        solve_start_time = time.time()

        # algorithm begin ---------------------------------------------
        self.solution.map_node_last = copy.deepcopy(self.solution.map_node) # Save previous data
        self.solution.map_link_last = copy.deepcopy(self.solution.map_link) # Save previous data
        
        pso = PSO(
    	    func=self.calc_fitness, 
    	    dim=self.service_chain.num_nodes*self.substrate_network.num_nodes,
            pop=10, 
    	    max_iter=20, 
    	    lb=[0]*(self.service_chain.num_nodes*self.substrate_network.num_nodes), 
    	    ub=[1]*(self.service_chain.num_nodes*self.substrate_network.num_nodes), 
    	    w=0.8,
    	    c1=0.5, 
    	    c2=0.5)
        pso.run()

        x = np.array(pso.gbest_x)
        x = x.reshape((self.service_chain.num_nodes,self.substrate_network.num_nodes))
        for v_node in self.service_chain.nodes:
            self.solution.map_node[v_node] = np.where(x[v_node,:]==np.max(x[v_node,:]))[0][0]

        for v_link in self.service_chain.edges():
            map_path = nx.dijkstra_path(self.substrate_network,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        
        # algorithm end ---------------------------------------------

        self.solution.current_description = self.__check_constraints(event)

        if self.solution.current_description == SOLUTION_TYPE.CHANGE_SUCCESS:
            self.solution.current_result = True
        else:
            self.solution.current_result = False

        self.__perform_measure(event)
        self.solution.cost_real_time = time.time()-solve_start_time

        return self.solution

    def solve_ending(self,event: Event) -> Solution:
        self.event = event
        self.service_chain = event.sfc
        self.substrate_network = event.current_substrate

        self.solution.current_time = event.time
        self.solution.current_service_chain = copy.deepcopy(event.sfc)
        self.solution.current_substrate_net = copy.deepcopy(event.current_substrate)

        solve_start_time = time.time()

        # algorithm begin ---------------------------------------------
        
        # self.solution.map_node_last = copy.deepcopy(self.solution.map_node) # Save previous data but not use
        # self.solution.map_link_last = copy.deepcopy(self.solution.map_link) # Save previous data but not use

        # algorithm end ----------------------------------------------

        self.solution.current_description = SOLUTION_TYPE.END_SUCCESS
        self.solution.current_result = True

        self.__perform_measure(event)

        self.solution.cost_real_time =  time.time()-solve_start_time

        return self.solution
    
    def calc_fitness(self,*Args):
        x = np.array(Args)
        x = x.reshape((self.service_chain.num_nodes,self.substrate_network.num_nodes))
        for v_node in self.service_chain.nodes:
            self.solution.map_node[v_node] = np.where(x[v_node,:]==np.max(x[v_node,:]))[0][0]

        for v_link in self.service_chain.edges():
            map_path = nx.dijkstra_path(self.substrate_network,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]

        if self.__check_constraints(self.event) not in (SOLUTION_TYPE.SET_SUCCESS,SOLUTION_TYPE.CHANGE_SUCCESS):
            return float("inf")
        else:
            perform_all_use_cpu_resource = sum(self.service_chain.get_all_nodes_attrs_values("cpu_setting"))
            perform_all_use_ram_resource = sum(self.service_chain.get_all_nodes_attrs_values("ram_setting"))
            perform_all_use_disk_resource = sum(self.service_chain.get_all_nodes_attrs_values("disk_setting"))
            perform_all_use_energy_resource = sum(self.service_chain.get_all_nodes_attrs_values("cpu_setting"))
            perform_all_use_link_resource = sum(self.service_chain.get_all_links_attrs_values("band_setting").values())/2
            perform_revenue_unit = \
                perform_all_use_cpu_resource * self.substrate_network.get_node_attrs_price("cpu_setting") + \
                perform_all_use_ram_resource * self.substrate_network.get_node_attrs_price("ram_setting") + \
                perform_all_use_disk_resource * self.substrate_network.get_node_attrs_price("disk_setting") + \
                perform_all_use_energy_resource * self.substrate_network.get_node_attrs_price("energy_setting") + \
                perform_all_use_link_resource * self.substrate_network.get_link_attrs_price("band_setting")
            
            perform_latency_run = self.__get_latency_running()
            perform_latency_map = self.__get_latency_remap()
            perform_latency_route = self.__get_latency_reroute()
            perform_latency = perform_latency_run + perform_latency_map + perform_latency_route

            return perform_revenue_unit * (perform_latency-self.service_chain.qos_latency)


    def __check_constraints(self, event: Event) -> SOLUTION_TYPE:
        # Node Resource Constraint Check
        remain_cpu_of_nodes = self.substrate_network.get_all_nodes_attrs_values("cpu_setting","remain_setting")
        remain_ram_of_nodes = self.substrate_network.get_all_nodes_attrs_values("ram_setting","remain_setting")
        remain_disk_of_nodes = self.substrate_network.get_all_nodes_attrs_values("disk_setting","remain_setting")
        remain_eng_of_nodes = self.substrate_network.get_all_nodes_attrs_values("energy_setting","remain_setting")

        for sfc_node, phy_node in self.solution.map_node.items():     
            request_cpu_of_node = self.service_chain.get_node_attrs_value(sfc_node,"cpu_setting")
            request_ram_of_node = self.service_chain.get_node_attrs_value(sfc_node,"ram_setting")
            request_disk_of_node = self.service_chain.get_node_attrs_value(sfc_node,"disk_setting")
            request_eng_of_node = request_cpu_of_node * (self.service_chain.endtime - self.solution.current_time)
            
            remain_cpu_of_nodes[phy_node] -= request_cpu_of_node
            if remain_cpu_of_nodes[phy_node] < 0:
                if event.type == EventType.SFC_ARRIVE:
                    return SOLUTION_TYPE.SET_NODE_FAILED_FOR_CPU
                elif event.type == EventType.TOPO_CHANGE:
                    return SOLUTION_TYPE.CHANGE_NODE_FAILED_FOR_CPU
            
            remain_ram_of_nodes[phy_node] -= request_ram_of_node
            if remain_ram_of_nodes[phy_node] < 0:
                if event.type == EventType.SFC_ARRIVE:
                    return SOLUTION_TYPE.SET_NODE_FAILED_FOR_RAM
                elif event.type == EventType.TOPO_CHANGE:
                    return SOLUTION_TYPE.CHANGE_NODE_FAILED_FOR_RAM
            
            remain_disk_of_nodes[phy_node] -= request_disk_of_node
            if remain_disk_of_nodes[phy_node] < 0:
                if event.type == EventType.SFC_ARRIVE:
                    return SOLUTION_TYPE.SET_NODE_FAILED_FOR_DISK
                elif event.type == EventType.TOPO_CHANGE:
                    return SOLUTION_TYPE.CHANGE_NODE_FAILED_FOR_DISK
            
            remain_eng_of_nodes[phy_node] -= request_eng_of_node
            if remain_eng_of_nodes[phy_node] < 0:
                if event.type == EventType.SFC_ARRIVE:
                    return SOLUTION_TYPE.SET_NODE_FAILED_FOR_ENG
                elif event.type == EventType.TOPO_CHANGE:
                    return SOLUTION_TYPE.CHANGE_NODE_FAILED_FOR_ENG
            
        # Link Resource Constraint Check
        remain_band_of_links = self.substrate_network.get_all_links_attrs_values("band_setting","remain_setting")
        # code.interact(banner="",local=locals())
        CHECK_FLAG = True
        for sfc_link, phy_links in self.solution.map_link.items():
            if CHECK_FLAG == False: break
            request_band_of_link = self.service_chain.get_link_attrs_value(sfc_link,"band_setting")
            for phy_link in phy_links:
                remain_band_of_links[phy_link] -= request_band_of_link
                if remain_band_of_links[phy_link] < 0:
                    CHECK_FLAG = False
                    break
        if CHECK_FLAG == False:
            if event.type == EventType.SFC_ARRIVE:
                return SOLUTION_TYPE.SET_LINK_FAILED
            elif event.type == EventType.TOPO_CHANGE:
                return SOLUTION_TYPE.CHANGE_LINK_FAILED
        
        # Qos Constraint Check
        if self.__get_latency_running() > event.sfc.qos_latency:
            if event.type == EventType.SFC_ARRIVE:
                return SOLUTION_TYPE.SET_LATENCY_FAILED
            elif event.type == EventType.TOPO_CHANGE:
                return SOLUTION_TYPE.CHANGE_LATENCY_FAILED
        
        # All check passed
        if event.type == EventType.SFC_ARRIVE:
            return SOLUTION_TYPE.SET_SUCCESS
        elif event.type == EventType.TOPO_CHANGE:
            return SOLUTION_TYPE.CHANGE_SUCCESS

    def __perform_measure(self,event: Event):
        perform_all_use_cpu_resource = sum(self.service_chain.get_all_nodes_attrs_values("cpu_setting"))
        perform_all_use_ram_resource = sum(self.service_chain.get_all_nodes_attrs_values("ram_setting"))
        perform_all_use_disk_resource = sum(self.service_chain.get_all_nodes_attrs_values("disk_setting"))
        perform_all_use_energy_resource = sum(self.service_chain.get_all_nodes_attrs_values("cpu_setting"))

        perform_all_use_link_resource = sum(self.service_chain.get_all_links_attrs_values("band_setting").values())/2
        # for sfd_link, phy_links in self.solution.map_link.items():
        #     perform_all_use_link_resource += self.service_chain.get_link_attrs_value(sfd_link,"band_setting") * len(phy_links)

        perform_all_phy_cpu_resource = sum(self.substrate_network.get_all_nodes_attrs_values("cpu_setting","max_setting"))
        perform_all_phy_ram_resource = sum(self.substrate_network.get_all_nodes_attrs_values("ram_setting","max_setting"))
        perform_all_phy_disk_resource = sum(self.substrate_network.get_all_nodes_attrs_values("disk_setting","max_setting"))
        perform_all_phy_energy_resource = sum(self.substrate_network.get_all_nodes_attrs_values("cpu_setting","max_setting"))
        perform_all_phy_link_resource = sum(self.substrate_network.get_all_links_attrs_values("band_setting","max_setting").values())/2

        
        self.solution.perform_latency_run = self.__get_latency_running()
        self.solution.perform_latency_map = self.__get_latency_remap()
        self.solution.perform_latency_route = self.__get_latency_reroute()
        self.solution.perform_latency = self.solution.perform_latency_run + self.solution.perform_latency_map + self.solution.perform_latency_route

        self.solution.perform_revenue_unit = perform_all_use_cpu_resource * self.substrate_network.get_node_attrs_price("cpu_setting") + \
                                            perform_all_use_ram_resource * self.substrate_network.get_node_attrs_price("ram_setting") + \
                                            perform_all_use_disk_resource * self.substrate_network.get_node_attrs_price("disk_setting") + \
                                            perform_all_use_energy_resource * self.substrate_network.get_node_attrs_price("energy_setting") + \
                                            perform_all_use_link_resource * self.substrate_network.get_link_attrs_price("band_setting")

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

    def __get_latency_remap(self) -> float:
        latency_list = []
        for vnf_node in self.solution.map_node.keys():
            if self.solution.map_node[vnf_node] != self.solution.map_node_last[vnf_node]:
                if vnf_node == 0:
                    latency_list.append(0)
                else:
                    latency_list.append(self.service_chain.get_node_attrs_value(vnf_node,"ram_setting") / self.service_chain.get_link_attrs_value((vnf_node-1,vnf_node),"band_setting"))
        return sum(latency_list)

    def __get_latency_reroute(self) -> float:
        REROUTE_TIME_UNIT = 0.01
        latency_list = []
        for vnf_link in self.solution.map_link.keys():
            vnf_link_diff = set(self.solution.map_link[vnf_link]) ^ set(self.solution.map_link_last[vnf_link])
            latency_list.append(len(vnf_link_diff)*REROUTE_TIME_UNIT)
        return sum(latency_list)

    @staticmethod
    def get_revenue(solution_group:SolutionGroup):
        revenue = 0
        time_list = [solution.current_time for solution in solution_group]
        for i in range(1,len(time_list),1):
            calculate_flag = solution_group[i-1].perform_latency < solution_group[i-1].current_service_chain.qos_latency
            calculate_time = time_list[i-1]+solution_group[i-1].perform_latency
            if calculate_time > time_list[i]: calculate_time = time_list[i]
            revenue = revenue + \
                      solution_group[i-1].perform_revenue_unit * (calculate_time-time_list[i-1]) * int(calculate_flag) + \
                      solution_group[i-1].perform_revenue_unit * (time_list[i]-calculate_time)
        return revenue


