#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   substrate_network.py
@Time    :   2024/01/11 22:29:06
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

import networkx as nx
from data import Config
from utils import NumberOperator
import logging

class SubstrateNetwork(nx.Graph):
    def __init__(self, config:Config):
        super(SubstrateNetwork, self).__init__()
       
        self.num_nodes: int = config.substrate_network_setting["num_nodes"]
        self.topology_setting: dict[dict] = config.substrate_network_setting["topology_setting"]
        self.node_attrs_setting: dict[dict] = config.substrate_network_setting["node_attrs_setting"]
        self.link_attrs_setting: dict[dict] = config.substrate_network_setting["link_attrs_setting"]

        # self.band_setting = self.link_attrs_setting["band_setting"]

        self.__generate_topology()
        self.__generate_node_attrs_data()


    def __generate_topology(self):
        assert self.num_nodes >= 1
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

        # 对于每一种资源执行
        for node_attrs_name in self.node_attrs_setting.keys():
            # 获取该资源的属性
            node_attrs_name_setting = self.node_attrs_setting[node_attrs_name]
            # 生成该资源的随机值数列
            node_attrs_name_value = NumberOperator.generate_data_with_distribution(self.num_nodes,**node_attrs_name_setting["max_setting"])

            # 对于每一个节点
            for node_index in range(self.num_nodes):
                self.node_attrs_setting[node_attrs_name]["max_setting"]["value"] = node_attrs_name_value[node_index]
                self.node_attrs_setting[node_attrs_name]["remain_setting"]["value"] = node_attrs_name_value[node_index]
                self.nodes[node_index][node_attrs_name] = self.node_attrs_setting[node_attrs_name]





