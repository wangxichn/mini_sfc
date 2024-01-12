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


class SubstrateNetwork(nx.Graph):
    def __init__(self, config:Config):
        super(SubstrateNetwork, self).__init__()
        # set graph attributes

        self.num_nodes = config.substrate_network_setting["num_nodes"]
        self.topology_setting = config.substrate_network_setting["topology_setting"]
        self.node_attrs_setting = config.substrate_network_setting["node_attrs_setting"]
        self.link_attrs_setting = config.substrate_network_setting["link_attrs_setting"]
        # self.create_attrs_from_setting()


