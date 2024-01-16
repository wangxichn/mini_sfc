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
from base import Event
import networkx as nx
import random
import code
import copy 

@SOLVER_REGISTRAR.regist(solver_name='baseline_random')
class BaselineRandom(Solver):
    def __init__(self) -> None:
        super().__init__()

    def initialize(self,event: Event) -> None:
        self.solution = Solution()
        self.service_chain = event.sfc
        self.substrate_network = event.current_substrate

    def solve_embedding(self,event: Event) -> Solution:
        self.service_chain = event.sfc
        self.substrate_network = event.current_substrate

        # algorithm begin
        self.solution.current_time = event.time
        self.solution.current_service_chain = event.sfc
        self.solution.current_substrate_net = copy.deepcopy(event.current_substrate)
        
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

        self.solution.current_description = SOLUTION_TYPE.SET_SUCCESS
        self.solution.current_result = True

        self.solution.perform_revenue = 0
        self.solution.perform_revenue_longterm = 0
        self.solution.perform_latency = 0
        self.solution.cost_real_time = 0
        self.solution.cost_node_resource = 0
        self.solution.cost_node_resource_percentage = 0
        self.solution.cost_link_resource = 0
        self.solution.cost_link_resource_percentage = 0

        return self.solution
    
    def solve_migration(self,event: Event) -> Solution:
        self.service_chain = event.sfc
        self.substrate_network = event.current_substrate

        self.solution = self.solve_embedding(event) # random migaration

        self.solution.current_description = SOLUTION_TYPE.CHANGE_SUCCESS

        return self.solution

    def solve_ending(self,event: Event) -> Solution:
        self.service_chain = event.sfc
        self.substrate_network = event.current_substrate

        self.solution.current_time = event.time
        self.solution.current_service_chain = event.sfc
        self.solution.current_substrate_net = copy.deepcopy(event.current_substrate)
        
        # continue using the last map solution
        self.solution.map_node = self.solution.map_node
        self.solution.map_link = self.solution.map_link

        self.solution.current_description = SOLUTION_TYPE.END_SUCCESS
        self.solution.current_result = True

        self.solution.perform_revenue = 0
        self.solution.perform_revenue_longterm = 0
        self.solution.perform_latency = 0
        self.solution.cost_real_time = 0
        self.solution.cost_node_resource = 0
        self.solution.cost_node_resource_percentage = 0
        self.solution.cost_link_resource = 0
        self.solution.cost_link_resource_percentage = 0

        return self.solution

