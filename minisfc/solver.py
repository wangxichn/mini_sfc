#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   solver.py
@Time    :   2024/06/18 15:32:23
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

import random
from enum import Enum, auto
from .event import Event, EventType
from .topo import SubstrateTopo, ServiceTopo, Topo
from .mano import NfvManager
import networkx as nx
import numpy as np
import code
import copy

class SOLUTION_TYPE(Enum):
    NOTHING = auto()
    SET_SUCCESS = auto()
    SET_FAILED_FOR_NODE_CPU = auto()
    SET_FAILED_FOR_NODE_RAM = auto()
    SET_FAILED_FOR_LINK_BAND = auto()
    SET_FAILED_FOR_LATENCY = auto()
    CHANGE_SUCCESS = auto()
    CHANGE_FAILED_FOR_NODE_CPU = auto()
    CHANGE_FAILED_FOR_NODE_RAM = auto()
    CHANGE_FAILED_FOR_LINK_BAND = auto()
    CHANGE_FAILED_FOR_LATENCY = auto()
    END_SUCCESS = auto()

class Solution:
    def __init__(self) -> None:
        self.current_result: bool = False
        self.current_description :SOLUTION_TYPE = SOLUTION_TYPE.NOTHING

        self.map_node: dict[int:int] = {}
        """dict[ServiceChain.node:SubstrateNetwork.node]
        Description: map from ServiceChain nodes to SubstrateNetwork nodes
        """

        self.map_link: dict[tuple[int,int]:list[tuple[int,int]]] = {}
        """dict[ServiceChain.link:list[SubstrateNetwork.link]]
        Description: map from ServiceChain links to SubstrateNetwork links
        """

        self.resource: dict[str:list[int]] = {}
        """dict[resource name:list[value]]
        Description: the resources allocated on each VNF and link in the ServiceChain
        """

class Solver:
    def __init__(self, substrateTopo:SubstrateTopo, serviceTopo:ServiceTopo) -> None:
        self.plan_substrateTopo = substrateTopo
        self.plan_serviceTopo = serviceTopo
    
        self.record_solutions:dict[int:list[Solution]] = {} # {sfcId:[solutions]}

    def initialize(self,nfvManager: NfvManager) -> None:
        self.nfvManager = nfvManager
    
    def solve_embedding(self,event: Event) -> Solution:
        return NotImplementedError
    
    def solve_migration(self,event: Event) -> Solution:
        return NotImplementedError
    
    def solve_ending(self,event: Event) -> Solution:
        return NotImplementedError
    
    def saveParam():
        pass

    def loadParam():
        pass

class RadomSolver(Solver):
    def __init__(self, substrateTopo: SubstrateTopo, serviceTopo: ServiceTopo) -> None:
        super().__init__(substrateTopo, serviceTopo)

    def initialize(self, nfvManager: NfvManager):
        super().initialize(nfvManager)
    
    def solve_embedding(self, event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        for v_node in self.sfcGraph.nodes:
            if v_node == 0:
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][0]
            elif v_node == (len(self.sfcGraph.nodes)-1):
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][1]
            else:
                self.solution.map_node[v_node] = random.sample(range(len(self.substrateTopo.nodes)),1)[0]

        for v_link in self.sfcGraph.edges():
            map_path = nx.dijkstra_path(self.substrateTopo,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        
        # If the fixed VNF resource allocation in the original SFC problem is used:
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        self.solution.resource['cpu'] = [self.nfvManager.vnfPoolDict[vnfId]['cpu'] for vnfId in vnfRequstList]
        self.solution.resource['ram'] = [self.nfvManager.vnfPoolDict[vnfId]['ram'] for vnfId in vnfRequstList]
        self.solution.resource['band'] = [self.nfvManager.vnfPoolDict[vnfRequstList[i],vnfRequstList[i+1]]['band'] 
                                          for i in range(len(vnfRequstList)-1)]

        # If the dynamic resource allocation of each VNF is implemented in the solver algorithm:
        # self.solution.resource['cpu'] = 
        # self.solution.resource['ram'] = 
        # self.solution.resource['band'] = 
        # algorithm end ---------------------------------------------

        self.solution.current_description = self.check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.SET_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True
        
        self.record_solutions[self.event.serviceTopoId]=[self.solution]

        return self.solution
    
    def solve_migration(self, event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        for v_node in self.sfcGraph.nodes:
            if v_node == 0:
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][0]
            elif v_node == (len(self.sfcGraph.nodes)-1):
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][1]
            else:
                self.solution.map_node[v_node] = random.sample(range(len(self.substrateTopo.nodes)),1)[0]

        for v_link in self.sfcGraph.edges():
            map_path = nx.dijkstra_path(self.substrateTopo,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        

        # If the fixed VNF resource allocation in the original SFC problem is used:
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        self.solution.resource['cpu'] = [self.nfvManager.vnfPoolDict[vnfId]['cpu'] for vnfId in vnfRequstList]
        self.solution.resource['ram'] = [self.nfvManager.vnfPoolDict[vnfId]['ram'] for vnfId in vnfRequstList]
        self.solution.resource['band'] = [self.nfvManager.vnfPoolDict[vnfRequstList[i],vnfRequstList[i+1]]['band'] 
                                          for i in range(len(vnfRequstList)-1)]

        # If the dynamic resource allocation of each VNF is implemented in the solver algorithm:
        # self.solution.resource['cpu'] = 
        # self.solution.resource['ram'] = 
        # self.solution.resource['band'] = 
        # algorithm end ---------------------------------------------

        self.solution.current_description = self.check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.CHANGE_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True
        
        self.record_solutions[self.event.serviceTopoId].append(self.solution)

        return self.solution
    
    def solve_ending(self, event: Event) -> Solution:
        self.event = event
        self.solution:Solution = copy.deepcopy(self.record_solutions[self.event.serviceTopoId][-1])
        self.solution.current_description = SOLUTION_TYPE.END_SUCCESS
        self.solution.current_result = True

        self.record_solutions[self.event.serviceTopoId].append(self.solution)

        return self.solution
    
    def check_constraints(self, event: Event) -> SOLUTION_TYPE:

        remain_cpu_of_nodes = self.substrateTopo.get_all_nodes_attrs_values('remain_cpu')
        remain_ram_of_nodes = self.substrateTopo.get_all_nodes_attrs_values('remain_ram')
        remain_band_of_links = self.substrateTopo.get_all_links_attrs_values('remain_band')

        for sfc_node, phy_node in self.solution.map_node.items():     
            request_cpu_of_node = self.solution.resource['cpu'][sfc_node]
            request_ram_of_node = self.solution.resource['ram'][sfc_node]

            remain_cpu_of_nodes[phy_node] -= request_cpu_of_node
            if remain_cpu_of_nodes[phy_node] < 0:
                if event.type == EventType.SFC_ARRIVE:
                    return SOLUTION_TYPE.SET_FAILED_FOR_NODE_CPU
                elif event.type == EventType.TOPO_CHANGE:
                    return SOLUTION_TYPE.CHANGE_FAILED_FOR_NODE_CPU
            
            remain_ram_of_nodes[phy_node] -= request_ram_of_node
            if remain_ram_of_nodes[phy_node] < 0:
                if event.type == EventType.SFC_ARRIVE:
                    return SOLUTION_TYPE.SET_FAILED_FOR_NODE_RAM
                elif event.type == EventType.TOPO_CHANGE:
                    return SOLUTION_TYPE.CHANGE_FAILED_FOR_NODE_RAM

        for sfc_link, phy_links in self.solution.map_link.items():
            request_band_of_link = self.solution.resource['band'][sfc_link[0]]
            for phy_link in phy_links:
                remain_band_of_links[phy_link] -= request_band_of_link
                if remain_band_of_links[phy_link] < 0:
                    if event.type == EventType.SFC_ARRIVE:
                        return SOLUTION_TYPE.SET_FAILED_FOR_LINK_BAND
                    elif event.type == EventType.TOPO_CHANGE:
                        return SOLUTION_TYPE.CHANGE_FAILED_FOR_LINK_BAND
        
        # Qos Constraint Check
        if self.get_latency_running() > event.serviceTopo.plan_qosRequesDict[event.serviceTopoId]:
            if event.type == EventType.SFC_ARRIVE:
                return SOLUTION_TYPE.SET_FAILED_FOR_LATENCY
            elif event.type == EventType.TOPO_CHANGE:
                return SOLUTION_TYPE.CHANGE_FAILED_FOR_LATENCY
        
        # All check passed
        if event.type == EventType.SFC_ARRIVE:
            return SOLUTION_TYPE.SET_SUCCESS
        elif event.type == EventType.TOPO_CHANGE:
            return SOLUTION_TYPE.CHANGE_SUCCESS

    def get_latency_running(self) -> float:
        latency_list = []
        for phy_link_list in self.solution.map_link.values():
            for phy_link in phy_link_list:
                latency_list.append(self.substrateTopo.edges[phy_link]['weight'])

        return sum(latency_list)


class GreedySolver(RadomSolver):
    def __init__(self, substrateTopo: SubstrateTopo, serviceTopo: ServiceTopo) -> None:
        super().__init__(substrateTopo, serviceTopo)
    
    def solve_embedding(self,event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        temp_subStrateTopo = copy.deepcopy(self.substrateTopo)

        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        self.solution.resource['cpu'] = [self.nfvManager.vnfPoolDict[vnfId]['cpu'] for vnfId in vnfRequstList]
        self.solution.resource['ram'] = [self.nfvManager.vnfPoolDict[vnfId]['ram'] for vnfId in vnfRequstList]
        self.solution.resource['band'] = [self.nfvManager.vnfPoolDict[vnfRequstList[i],vnfRequstList[i+1]]['band'] 
                                          for i in range(len(vnfRequstList)-1)]

        for v_node in self.sfcGraph.nodes:
            if v_node == 0:
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][0]
            elif v_node == (len(self.sfcGraph.nodes)-1):
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][1]
            else:
                subStrateResource_cpu = temp_subStrateTopo.get_all_nodes_attrs_values('remain_cpu')
                subStrateResource_ram = temp_subStrateTopo.get_all_nodes_attrs_values('remain_ram')
                subStrateResource = (np.array(subStrateResource_cpu)+np.array(subStrateResource_ram)).tolist()
                self.solution.map_node[v_node] = subStrateResource.index(max(subStrateResource))
                temp_subStrateTopo.opt_node_attrs_value(self.solution.map_node[v_node],'remain_cpu','decrease',self.solution.resource['cpu'][v_node])
                temp_subStrateTopo.opt_node_attrs_value(self.solution.map_node[v_node],'remain_ram','decrease',self.solution.resource['ram'][v_node])

        for v_link in self.sfcGraph.edges():
            map_path = nx.dijkstra_path(self.substrateTopo,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        # algorithm end ---------------------------------------------

        self.solution.current_description = self.check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.SET_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True
        
        self.record_solutions[self.event.serviceTopoId]=[self.solution]
        
        return self.solution
    
    def solve_migration(self,event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        temp_subStrateTopo = copy.deepcopy(self.substrateTopo)

        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        self.solution.resource['cpu'] = [self.nfvManager.vnfPoolDict[vnfId]['cpu'] for vnfId in vnfRequstList]
        self.solution.resource['ram'] = [self.nfvManager.vnfPoolDict[vnfId]['ram'] for vnfId in vnfRequstList]
        self.solution.resource['band'] = [self.nfvManager.vnfPoolDict[vnfRequstList[i],vnfRequstList[i+1]]['band'] 
                                          for i in range(len(vnfRequstList)-1)]

        for v_node in self.sfcGraph.nodes:
            if v_node == 0:
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][0]
            elif v_node == (len(self.sfcGraph.nodes)-1):
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][1]
            else:
                subStrateResource_cpu = temp_subStrateTopo.get_all_nodes_attrs_values('remain_cpu')
                subStrateResource_ram = temp_subStrateTopo.get_all_nodes_attrs_values('remain_ram')
                subStrateResource = (np.array(subStrateResource_cpu)+np.array(subStrateResource_ram)).tolist()
                self.solution.map_node[v_node] = subStrateResource.index(max(subStrateResource))
                temp_subStrateTopo.opt_node_attrs_value(subStrateResource,'remain_cpu','decrease',self.solution.resource['cpu'][v_node])
                temp_subStrateTopo.opt_node_attrs_value(subStrateResource,'remain_ram','decrease',self.solution.resource['ram'][v_node])

        for v_link in self.sfcGraph.edges():
            map_path = nx.dijkstra_path(self.substrateTopo,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        # algorithm end ---------------------------------------------

        self.solution.current_description = self.check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.CHANGE_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True
        
        self.record_solutions[self.event.serviceTopoId].append(self.solution)

        return self.solution
    
