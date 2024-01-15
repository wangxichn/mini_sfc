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
from solvers import Solution
from typing import Tuple
import code

class VnffgManager:
    def __init__(self,service_chain:ServiceChain, substrate_network:SubstrateNetwork, **kwargs) -> None:
        self.setting = kwargs
        
        self.service_chain = service_chain
        self.vnf_num = service_chain.num_nodes
        self.vnf_group:list[NfvManager] = [NfvManager(**service_chain.nodes[i]) for i in service_chain.nodes]

        self.substrate_network = substrate_network

        self.solver_name = self.setting.get("solver_name","baseline_random")
        self.solver = SOLVER_REGISTRAR.get(self.solver_name)

    def handle_arrive(self) -> Tuple[SubstrateNetwork,Solution]:
        return self.substrate_network,Solution()

    def handle_ending(self) -> Tuple[SubstrateNetwork,Solution]:
        return self.substrate_network,Solution()

    def handle_topochange(self) -> Tuple[SubstrateNetwork,Solution]:
        return self.substrate_network,Solution()


