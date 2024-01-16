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
from mano import NfvManager
from solvers import SOLVER_REGISTRAR
from solvers import Solution,SolutionGroup
from typing import Tuple
import code

class VnffgManager:
    def __init__(self,service_chain:ServiceChain, substrate_network:SubstrateNetwork, **kwargs) -> None:
        self.setting = kwargs
        
        # Service Function Chain Property
        self.service_chain = service_chain
        self.vnf_num = service_chain.num_nodes
        self.vnf_group:list[NfvManager] = [NfvManager(**service_chain.nodes[i]) for i in service_chain.nodes]

        # Substrate Network Property
        self.substrate_network = substrate_network

        # Solver Property
        self.solver_name = self.setting.get("solver_name","baseline_random")
        self.solver = SOLVER_REGISTRAR.get(self.solver_name)()
        self.solver.initialize(self.service_chain,self.substrate_network)
        self.solution_group = SolutionGroup()


    def handle_arrive(self, service_chain:ServiceChain, substrate_network:SubstrateNetwork) -> Tuple[SubstrateNetwork,Solution]:
        self.solution_group.append(self.solver.solve_embedding(service_chain,substrate_network))

        # put the service_chain into substrate_network

        return self.substrate_network,self.solution_group[-1]

    def handle_ending(self, service_chain:ServiceChain, substrate_network:SubstrateNetwork) -> Tuple[SubstrateNetwork,Solution]:
        solution = Solution() # ending solution
        self.solution_group.append(solution)
        
        # remove the service_chain from substrate_network

        return self.substrate_network,self.solution_group[-1]

    def handle_topochange(self, service_chain:ServiceChain, substrate_network:SubstrateNetwork) -> Tuple[SubstrateNetwork,Solution]:
        self.solution_group.append(self.solver.solve_migration(service_chain,substrate_network))

        # dealwith the service_chain migration

        return self.substrate_network,self.solution_group[-1]


