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
import numpy as np
import logging
import code
import copy

class SubstrateNetwork(nx.Graph):
    def __init__(self, config:Config):
        super().__init__()
       
        self.num_nodes: int = config.substrate_network_setting["num_nodes"]
        self.topology_setting: dict = config.substrate_network_setting["topology_setting"]
        self.topology_change_setting: dict =  config.substrate_network_setting["topology_change_setting"]
        self.node_attrs_setting: dict[dict] = config.substrate_network_setting["node_attrs_setting"]
        self.link_attrs_setting: dict[dict] = config.substrate_network_setting["link_attrs_setting"]
        self.intralink_attrs_setting: dict[dict] = config.substrate_network_setting["intralink_attrs_setting"]

        self.__generate_topology()
        self.__generate_node_attrs_data()
        self.__generate_link_attrs_data()
        self.__generate_intralink_attrs_data()


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
        
        # There are internal links in the nodes of the substrate network 
        for i in range(self.num_nodes):
            G.add_edge(i,i)
        
        self.__dict__['_node'] = G.__dict__['_node']
        self.__dict__['_adj'] = G.__dict__['_adj']

    
    def __generate_node_attrs_data(self):
        for node_attrs_name in self.node_attrs_setting.keys():
            node_attrs_name_setting = self.node_attrs_setting[node_attrs_name]
            node_attrs_name_value = NumberOperator.generate_data_with_distribution(self.num_nodes,**node_attrs_name_setting["max_setting"])

            for node_id in range(self.num_nodes):
                self.node_attrs_setting[node_attrs_name]["max_setting"]["value"] = node_attrs_name_value[node_id]
                self.node_attrs_setting[node_attrs_name]["remain_setting"]["value"] = node_attrs_name_value[node_id]
                self.nodes[node_id][node_attrs_name] = copy.deepcopy(self.node_attrs_setting[node_attrs_name])


    def __generate_link_attrs_data(self):
        for link_attrs_name in self.link_attrs_setting.keys():
            link_attrs_name_setting = self.link_attrs_setting[link_attrs_name]
            link_attrs_name_value = NumberOperator.generate_data_with_distribution(len(self.edges),**link_attrs_name_setting["max_setting"])

            for edge_temp in self.edges:
                if edge_temp[0] != edge_temp[1]:
                    self.link_attrs_setting[link_attrs_name]["max_setting"]["value"] = link_attrs_name_value[0]
                    self.link_attrs_setting[link_attrs_name]["remain_setting"]["value"] = link_attrs_name_value[0]
                    self.edges[edge_temp][link_attrs_name] = copy.deepcopy(self.link_attrs_setting[link_attrs_name])
                    link_attrs_name_value.pop(0)

    def __generate_intralink_attrs_data(self):
        for link_attrs_name in self.intralink_attrs_setting.keys():
            link_attrs_name_setting = self.intralink_attrs_setting[link_attrs_name]
            link_attrs_name_value = NumberOperator.generate_data_with_distribution(len(self.edges),**link_attrs_name_setting["max_setting"])

            for edge_temp in self.edges:
                if edge_temp[0] == edge_temp[1]:
                    self.intralink_attrs_setting[link_attrs_name]["max_setting"]["value"] = link_attrs_name_value[0]
                    self.intralink_attrs_setting[link_attrs_name]["remain_setting"]["value"] = link_attrs_name_value[0]
                    self.edges[edge_temp][link_attrs_name] = copy.deepcopy(self.intralink_attrs_setting[link_attrs_name])
                    link_attrs_name_value.pop(0)

    def get_node_attrs_value(self, node_id:int, node_attrs_name:str, value_type:str) -> int:
        """Get the attribute values of a node

        Args:
            node_id (int): Networkx index of node
            node_attrs_name (str): "cpu_setting","ram_setting","disk_setting","energy_setting"
            value_type (str): "max_setting","remain_setting"

        Returns:
            int: value
        """

        return self.nodes[node_id][node_attrs_name][value_type]["value"]


    def get_all_nodes_attrs_values(self, node_attrs_name:str, value_type:str) -> list[int]:
        """Get the attribute values of all nodes in network

        Args:
            node_attrs_name (str): "cpu_setting","ram_setting","disk_setting","energy_setting"
            value_type (str): "max_setting","remain_setting"

        Returns:
            list[int]: values
        """

        return [self.nodes[node_id][node_attrs_name][value_type]["value"] for node_id in self.nodes]
    

    def get_node_attrs_price(self, node_attrs_name:str) -> int:
        """Get the attribute price of a node

        Args:
            node_attrs_name (str): "cpu_setting","ram_setting","disk_setting","energy_setting"

        Returns:
            int: price
        """

        return self.node_attrs_setting[node_attrs_name]["price"]


    def get_link_attrs_value(self, link_id:tuple[int,int], link_attrs_name:str, value_type:str) -> int:
        """Get the attribute values of a link

        Args:
            link_id (tuple[int,int]): Networkx index of link
            link_attrs_name (str): "band_setting"
            value_type (str): "max_setting","remain_setting"

        Returns:
            int: value
        """

        return self.edges[link_id][link_attrs_name][value_type]["value"]
    

    def get_all_links_attrs_values(self, link_attrs_name:str, value_type:str) -> list[int]:
        """Get the attribute values of all links in network

        Args:
            link_attrs_name (str): "band_setting"
            value_type (str): "max_setting","remain_setting"

        Returns:
            list[int]: values
        """

        return [self.edges[link_id][link_attrs_name][value_type]["value"] for link_id in self.edges]
    

    def get_link_attrs_price(self, link_attrs_name:str) -> int:
        """Get the attribute price of a link

        Args:
            link_attrs_name (str): "band_setting"

        Returns:
            int: price
        """

        return self.link_attrs_setting[link_attrs_name]["price"]


    def set_node_attrs_value(self, node_id:int, node_attrs_name:str, value_type:str, value:int):
        """Set the attribute values of a node

        Args:
            node_id (int): Networkx index of node
            node_attrs_name (str): "cpu_setting","ram_setting","disk_setting","energy_setting"
            value_type (str): "max_setting","remain_setting"
            value (int): number
        """

        self.nodes[node_id][node_attrs_name][value_type]["value"] = value

    def reduce_node_attrs_value(self, node_id:int, node_attrs_name:str, value_type:str, value:int):
        """Reduce the attribute values of a node

        Args:
            node_id (int): Networkx index of node
            node_attrs_name (str): "cpu_setting","ram_setting","disk_setting","energy_setting"
            value_type (str): "max_setting","remain_setting"
            value (int): number
        """

        remain_value = self.get_node_attrs_value(node_id,node_attrs_name,value_type)
        new_value = remain_value - value
        self.set_node_attrs_value(node_id,node_attrs_name,value_type,new_value)
    
    def increase_node_attrs_value(self, node_id:int, node_attrs_name:str, value_type:str, value:int):
        """Increase the attribute values of a node

        Args:
            node_id (int): Networkx index of node
            node_attrs_name (str): "cpu_setting","ram_setting","disk_setting","energy_setting"
            value_type (str): "max_setting","remain_setting"
            value (int): number
        """

        remain_value = self.get_node_attrs_value(node_id,node_attrs_name,value_type)
        new_value = remain_value + value
        self.set_node_attrs_value(node_id,node_attrs_name,value_type,new_value)
    
    def set_link_attrs_value(self, link_id:tuple[int,int], link_attrs_name:str, value_type:str, value:int):
        """Set the attribute values of a link

        Args:
            link_id (tuple[int,int]): Networkx index of link
            link_attrs_name (str): "band_setting"
            value_type (str): "max_setting","remain_setting"
            value (int): number
        """

        self.edges[link_id][link_attrs_name][value_type]["value"] = value

    def get_node_candidates_list(self, request_cpu, request_ram, request_disk, request_eng) -> list[int]:
        cpu_values = self.get_all_nodes_attrs_values("cpu_setting","remain_setting")
        ram_values = self.get_all_nodes_attrs_values("ram_setting","remain_setting")
        disk_values = self.get_all_nodes_attrs_values("disk_setting","remain_setting")
        eng_values = self.get_all_nodes_attrs_values("eng_setting","remain_setting")
        cadidates_node = []
        for node in self.nodes():
            if request_cpu <= cpu_values[node] and request_ram <= ram_values[node] and \
               request_disk <= disk_values[node] and request_eng <= eng_values[node]:
                cadidates_node.append(node)
        return cadidates_node
    
    def get_node_latency_from_mat(self, node_id:int, mat:np.ndarray):
        """ Get the wait time required to deploy VNF on this node with wait-matrix

        Args:
            node_id (int): 
            mat (np.ndarray): wait-matrix

        Returns:
            wait_time (Any): the entry of the matrix 

        Description:
            This function prepares algorithms that use a device 
            latency matrix, where the vertical matrix is the number 
            of CPU resources remaining in the device, the horizontal 
            matrix is the number of RAM resources remaining, and the 
            elements of the matrix are delay times 
        """

        return mat[self.get_node_attrs_value(node_id,"cpu_setting","remain_setting"),
                   self.get_node_attrs_value(node_id,"ram_setting","remain_setting")]

    def get_node_rank_by_attrs(self, node_attrs_name:str, value_type:str) -> list[int]:
        """Get the sequence sorted by the number of node resources in the network

        Args:
            node_attrs_name (str): "cpu_setting","ram_setting","disk_setting","energy_setting",
                                   "sum_setting"
            value_type (str): "max_setting","remain_setting"

        Returns:
            list[int]: Sorted node number sequence
        """
        
        if node_attrs_name == "sum_setting":
            nodes_value = (np.array(self.get_all_nodes_attrs_values("cpu_setting",value_type)) + \
                           np.array(self.get_all_nodes_attrs_values("ram_setting",value_type)) + \
                           np.array(self.get_all_nodes_attrs_values("disk_setting",value_type)) + \
                           np.array(self.get_all_nodes_attrs_values("energy_setting",value_type))).tolist()
        else:
            nodes_value = self.get_all_nodes_attrs_values(node_attrs_name,value_type)

        sorted_id = sorted(range(len(nodes_value)), key=lambda k: nodes_value[k], reverse=True)

        return sorted_id

    def get_adjacency_matrix(self):

        return np.array(nx.adjacency_matrix(self).todense())
    
    def change_topology(self):
        type = self.topology_change_setting["type"]
        assert type in ['random','aim'], ValueError('Unsupported graph type!')
        
        if type == 'random':
            break_prob = self.topology_change_setting.get('break_prob', 0.2)
            connect_prob = self.topology_change_setting.get('connect_prob', 0.2)
            adjacency_matrix_save = self.get_adjacency_matrix()

            connected = False
            while not connected:
                adjacency_matrix_temp = copy.deepcopy(adjacency_matrix_save)
                data_setting = {"dtype":"float", "high":1, "low":0, "distribution":"uniform"}
                random_number_array = np.array(NumberOperator.generate_data_with_distribution(self.num_nodes*self.num_nodes,**data_setting)).reshape((self.num_nodes,self.num_nodes))
                
                for i in range(self.num_nodes):
                    for j in range(i):
                        # if the origin link is break
                        if adjacency_matrix_save[i,j] == 0:
                            if random_number_array[i,j] <= connect_prob:
                                adjacency_matrix_temp[i,j] = adjacency_matrix_temp[j,i] = 1
                        # if the origin link is connect
                        elif adjacency_matrix_save[i,j] == 1:
                            if random_number_array[i,j] <= break_prob:
                                adjacency_matrix_temp[i,j] = adjacency_matrix_temp[j,i] = 0
                
                network_temp = nx.from_numpy_array(adjacency_matrix_temp)
                connected = nx.is_connected(network_temp)
            self.__change_topology_with_adjacency(adjacency_matrix_temp)
            
        else:
            raise NotImplementedError
        

        
    def __change_topology_with_adjacency(self,aim_adjacency_matrix):
        origin_adjacency_matrix = self.get_adjacency_matrix()
        for i in range(self.num_nodes):
            for j in range(i):
                # break old link
                if origin_adjacency_matrix[i,j]-aim_adjacency_matrix[i,j] == 1:
                    self.remove_edge(i,j)
                # connect new link
                elif aim_adjacency_matrix[i,j]-origin_adjacency_matrix[i,j] == 1:
                    for link_attrs_name in self.link_attrs_setting.keys():
                        link_attrs_name_setting = self.link_attrs_setting[link_attrs_name]
                        link_attrs_name_value = NumberOperator.generate_data_with_distribution(1,**link_attrs_name_setting["max_setting"])

                        self.link_attrs_setting[link_attrs_name]["max_setting"]["value"] = link_attrs_name_value[0]
                        self.link_attrs_setting[link_attrs_name]["remain_setting"]["value"] = link_attrs_name_value[0]
                        self.add_edges_from([(i,j,copy.deepcopy(self.link_attrs_setting))])


