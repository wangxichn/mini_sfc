#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   solution.py
@Time    :   2024/01/15 14:56:10
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from enum import Enum, auto
from data import ServiceChain
from data import SubstrateNetwork

class SOLUTION_TYPE(Enum):
    NOTHING = auto()
    SET_SUCCESS = auto()
    SET_NODE_FAILED_FOR_CPU = auto()
    SET_NODE_FAILED_FOR_RAM = auto()
    SET_NODE_FAILED_FOR_DISK = auto()
    SET_NODE_FAILED_FOR_ENG = auto()
    SET_LINK_FAILED = auto()
    SET_LATENCY_FAILED = auto()
    CHANGE_SUCCESS = auto()
    CHANGE_NODE_FAILED_FOR_CPU = auto()
    CHANGE_NODE_FAILED_FOR_RAM = auto()
    CHANGE_NODE_FAILED_FOR_DISK = auto()
    CHANGE_NODE_FAILED_FOR_ENG = auto()
    CHANGE_LINK_FAILED = auto()
    CHANGE_LATENCY_FAILED = auto()
    END_SUCCESS = auto()
    END_FAILED = auto()

class Solution:
    def __init__(self) -> None:
        self.current_result: bool = None
        self.current_description :SOLUTION_TYPE = SOLUTION_TYPE.NOTHING
        self.current_time: float = None
        self.current_substrate_net: SubstrateNetwork = None
        self.current_service_chain: ServiceChain = None

        self.map_node: dict[int:int] = {}
        """dict[ServiceChain.node:SubstrateNetwork.node]
        Description: map from ServiceChain nodes to SubstrateNetwork nodes
        """

        self.map_link: dict[tuple[int,int]:list[tuple[int,int]]] = {}
        """dict[ServiceChain.link:list[SubstrateNetwork.link]]
        Description: map from ServiceChain links to SubstrateNetwork links
        """

        self.map_node_last: dict[int:int] = {}
        """dict[ServiceChain.node:SubstrateNetwork.node]
        Description: map from ServiceChain nodes to SubstrateNetwork nodes last time 
        """

        self.map_link_last: dict[tuple[int,int]:list[tuple[int,int]]] = {}
        """dict[ServiceChain.link:list[SubstrateNetwork.link]]
        Description: map from ServiceChain links to SubstrateNetwork links last time
        """

        self.perform_revenue_unit = None
        """int
        Description: Revenue units are calculated for each event, reflecting how much 
            resources are used, regardless of the time of use 
        """

        self.perform_revenue = None
        """float
        Description:  Only at the normal end of the service will be calculated by the 
            embedded algorithm performed, by QoS decision specific revenue situation, 
            related to the service time  
        """

        self.perform_latency = None
        self.perform_latency_run = None
        self.perform_latency_map = None
        self.perform_latency_route = None
        self.cost_real_time = None
        self.cost_node_resource = None
        self.cost_node_resource_percentage = None
        self.cost_link_resource = None
        self.cost_link_resource_percentage = None


class SolutionGroup(list[Solution]):
    def __init_subclass__(cls) -> None:
        return super().__init_subclass__()
    
    def append(self, __object: Solution) -> None:
        return super().append(__object)