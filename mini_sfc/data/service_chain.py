#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   service_chain.py
@Time    :   2024/01/12 20:21:15
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   
             The structure of the service function chain is expressed as: 
             ----    -----       -----    ----
             |ap| -- |vnf| -...- |vnf| -- |ap|
             ----    -----       -----    ----
             'ap' indicates the access point using this service function chain.
              The creation of an access point does not use resources on any physical node, 
              only needs to indicate its mapping relationship with the physical node.

             'vnf' represents a virtual node in the service function chain that 
             needs to occupy physical node resources. The mapping relationship between it 
             and physical nodes has MANO dynamic arrangement 
'''

import networkx as nx
from data import Config
from utils import NumberOperator
import numpy as np
import code
import copy

class ServiceChain(nx.Graph):
    def __init__(self, config:Config, **kwargs):
        super().__init__()

        self.num_nodes_setting: dict = config.service_chain_setting["num_nodes_setting"]
        self.topology_setting: dict = config.service_chain_setting["topology_setting"]
        self.node_attrs_setting: dict[dict] = config.service_chain_setting["node_attrs_setting"]
        self.link_attrs_setting: dict[dict] = config.service_chain_setting["link_attrs_setting"]

        self.num_nodes: int = NumberOperator.generate_data_with_distribution(1,**self.num_nodes_setting)[0]

        self.id = kwargs.get("id",0)
        self.arrivetime = kwargs.get("arrivetime",0)
        self.lifetime = kwargs.get("lifetime",0)
        self.endtime = self.arrivetime + self.lifetime

        # set the ap nodes mapping relationship with the physical nodes
        self.ap_map = np.random.choice(range(config.substrate_network_setting["num_nodes"]),2)

        self.__generate_topology()
        self.__generate_node_attrs_data()
        self.__generate_link_attrs_data()


    def __generate_topology(self):
        #  A service function chain requires at least two nodes: access points
        assert self.num_nodes >= 2
        type = self.topology_setting["type"]
        assert type in ['path', 'star', 'waxman', 'random'], ValueError('Unsupported graph type!')
        
        if type == 'path':
            G = nx.path_graph(self.num_nodes)
        elif type == 'star':
            G = nx.star_graph(self.num_nodes)
        elif type == 'waxman':
            wm_alpha = self.topology_setting.get('wm_alpha', 0.5)
            wm_beta = self.topology_setting.get('wm_beta', 0.2)
            not_connected = True
            while not_connected:
                G = nx.waxman_graph(self.num_nodes, wm_alpha, wm_beta)
                not_connected = not nx.is_connected(G)
        else:
            raise NotImplementedError
        
        self.__dict__['_node'] = G.__dict__['_node']
        self.__dict__['_adj'] = G.__dict__['_adj'] 


    def __generate_node_attrs_data(self):
        for node_attrs_name in self.node_attrs_setting.keys():
            node_attrs_name_setting = self.node_attrs_setting[node_attrs_name]
            node_attrs_name_value = NumberOperator.generate_data_with_distribution(self.num_nodes,**node_attrs_name_setting)

            # Two access points do not use resources on physical node
            node_attrs_name_value[0] = node_attrs_name_value[-1] = 0
            
            for node_id in range(self.num_nodes):
                self.node_attrs_setting[node_attrs_name]["value"] = node_attrs_name_value[node_id]
                self.nodes[node_id][node_attrs_name] = copy.deepcopy(self.node_attrs_setting[node_attrs_name])


    def __generate_link_attrs_data(self):
        for link_attrs_name in self.link_attrs_setting.keys():
            link_attrs_name_setting = self.link_attrs_setting[link_attrs_name]
            link_attrs_name_value = NumberOperator.generate_data_with_distribution(len(self.edges),**link_attrs_name_setting)

            for edge_temp in self.edges:
                self.link_attrs_setting[link_attrs_name]["value"] = link_attrs_name_value[0]
                self.edges[edge_temp][link_attrs_name] = copy.deepcopy(self.link_attrs_setting[link_attrs_name])
                link_attrs_name_value.pop(0)

    def get_node_attrs_value(self, node_id:int, node_attrs_name:str) -> int:
        """Get the attribute values of a node

        Args:
            node_id (int): Networkx index of node
            node_attrs_name (str): "cpu_setting","ram_setting","disk_setting"

        Returns:
            int: value
        """

        return self.nodes[node_id][node_attrs_name]["value"]
    

    def get_link_attrs_value(self, link_id:tuple[int,int], link_attrs_name:str) -> int:
        """Get the attribute values of a link

        Args:
            link_id (tuple[int,int]): Networkx index of link
            link_attrs_name (str): "band_setting"

        Returns:
            int: value
        """

        return self.edges[link_id][link_attrs_name]["value"]
    
