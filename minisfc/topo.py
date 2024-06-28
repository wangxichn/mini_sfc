#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   topo.py
@Time    :   2024/06/17 19:44:24
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

import networkx as nx
import numpy as np

class Topo(nx.Graph):
    def __init__(self):
        super().__init__()
    
    def opt_node_attrs_value(self, node_id:int, node_attrs_name:str, opration:str, value=0) -> int:
        """Get the attribute values of a node

        Args:
            node_id (int): Networkx index of node
            node_attrs_name (str): "capacity/remain/request"+"_"+"cpu/ram"
            opration (str): "get/set/decrease/increase"
            value(int): opration aim value
        Returns:
            int: value
        """
        remain_value = self.nodes[node_id][node_attrs_name]

        if opration == "get":
            return remain_value
        elif opration == "set":
            self.nodes[node_id][node_attrs_name] = value
        elif opration == "decrease":
            self.nodes[node_id][node_attrs_name] = remain_value - value
        elif opration == "increase":
            self.nodes[node_id][node_attrs_name] = remain_value + value
        
        return self.nodes[node_id][node_attrs_name]
    
    def get_all_nodes_attrs_values(self, node_attrs_name:str) -> list[int]:
        """Get the attribute values of all nodes in network

        Args:
            node_attrs_name (str): "capacity/remain/request"+"_"+"cpu/ram"

        Returns:
            list[int]: values
        """

        return [self.nodes[node_id][node_attrs_name] for node_id in self.nodes]
    
    def get_all_nodes_aggrlinks_attrs_values(self, link_attrs_name:str) -> list[int]:
        """Get the attribute values ​​of the links around all node aggregates

        Args:
            link_attrs_name (str): "capacity/remain/request"+"_"+"band"

        Returns:
            list[int]: values
        """

        links_aggr_attrs_of_nodes = []
        adjacency_mat = self.get_adjacency_matrix()

        for i in range(len(self.nodes)):
            sum_temp = 0
            for j in range(len(self.nodes)):
                if adjacency_mat[i,j] == 1:
                    sum_temp += self.opt_link_attrs_value((i,j),link_attrs_name,'get')
            links_aggr_attrs_of_nodes.append(sum_temp)

        return links_aggr_attrs_of_nodes
    
    def opt_link_attrs_value(self, link_id:tuple[int,int], link_attrs_name:str, opration:str, value=0) -> int:
        """Get the attribute values of a link

        Args:
            link_id (tuple[int,int]): Networkx index of link
            link_attrs_name (str): "capacity/remain/request"+"_"+"band"
            opration (str): "get/set/decrease/increase"
            value(int): opration aim value
        Returns:
            int: value
        """

        remain_value = self.edges[link_id][link_attrs_name]

        if opration == "get":
            return remain_value
        elif opration == "set":
            self.edges[link_id][link_attrs_name] = value
        elif opration == "decrease":
            self.edges[link_id][link_attrs_name] = remain_value - value
        elif opration == "increase":
            self.edges[link_id][link_attrs_name] = remain_value + value
        
        return self.edges[link_id][link_attrs_name]

    
    def get_all_links_attrs_values(self, link_attrs_name:str) -> dict[tuple[int,int]:int]:
        """Get the attribute values of all links in network

        Args:
            link_attrs_name (str): "capacity/remain/request"+"_"+"band"

        Returns:
            dict[tuple[int,int]:int]: edge:value
        """
        link_dict = {}
        for edge in self.edges:
            link_dict[(edge[0],edge[1])] = link_dict[(edge[1],edge[0])] = self.edges[edge][link_attrs_name]

        return link_dict

    def get_sum_resource_list(self, attrs_name:str):
        """Get the sum of attribute values of network

        Args:
            attrs_name (str): "capacity/remain/request"

        Returns:
            list[int,int,int]: value
        """
        cpu_resource = sum(self.get_all_nodes_attrs_values(attrs_name+'_cpu'))
        ram_resource = sum(self.get_all_nodes_attrs_values(attrs_name+'_ram'))
        band_resource = sum(self.get_all_links_attrs_values(attrs_name+'_band').values())
        return [cpu_resource,ram_resource,band_resource]
    
    def get_adjacency_matrix(self):
        return np.array(nx.adjacency_matrix(self,weight=None).todense())
    
    def get_kshortest_paths(self, source, target, k):
        from itertools import islice
        return list(islice(nx.shortest_simple_paths(self, source, target, weight='weight'), k))
        

class SubstrateTopo(Topo):
    def __init__(self,timeList:list[float],adjacencyMatDict:dict[float:np.ndarray],weightMatDict:dict[float:np.ndarray],
                 nodeResourceDict:dict[float,str:np.ndarray],linkResourceDict:dict[float,str:np.ndarray]):
        """_summary_

        Args:
            timeList (list[float]): [time]
            adjacencyMatDict (dict[float:np.ndarray]): {time:adjacencyMat}
            weightMatDict (dict[float:np.ndarray]): {time:weightMat}
            nodeResourceDict (dict[float,str:np.ndarray]): {time,resourcetype:valueArray}
            linkResourceDict (dict[float,str:np.ndarray]): {time,resourcetype:valueMat}
        """
        super().__init__()

        self.plan_changeTimeList = timeList
        self.plan_adjacencyMatDict = adjacencyMatDict
        self.plan_weightMatDict = weightMatDict
        self.plan_nodeResourceDict = nodeResourceDict
        self.plan_linkResourceDict = linkResourceDict

        # init the substrate topo at time 0 for ready
        self.graph['time'] = self.plan_changeTimeList[0]
        G = nx.from_numpy_array(self.plan_adjacencyMatDict[self.graph['time']])
        self.__dict__['_node'] = G.__dict__['_node']
        self.__dict__['_adj'] = G.__dict__['_adj']
        
        for node_id in range(len(self.nodes)):
            self.nodes[node_id]["capacity_cpu"] = self.plan_nodeResourceDict[self.graph['time'],'cpu'][node_id]
            self.nodes[node_id]["capacity_ram"] = self.plan_nodeResourceDict[self.graph['time'],'ram'][node_id]
            self.nodes[node_id]["remain_cpu"] = self.plan_nodeResourceDict[self.graph['time'],'cpu'][node_id]
            self.nodes[node_id]["remain_ram"] = self.plan_nodeResourceDict[self.graph['time'],'ram'][node_id]

        for edge_temp in self.edges:
            self.edges[edge_temp]['weight'] = self.plan_weightMatDict[self.graph['time']][edge_temp[0],edge_temp[1]]
            self.edges[edge_temp]["capacity_band"] = self.plan_linkResourceDict[self.graph['time'],'band'][edge_temp[0],edge_temp[1]]
            self.edges[edge_temp]["remain_band"] = self.plan_linkResourceDict[self.graph['time'],'band'][edge_temp[0],edge_temp[1]]

    def changeTopo(self,time):
        assert time in self.plan_changeTimeList, ValueError('The timing of the topology change is not within expectations!')

        self.graph['time'] = time
        origin_adjacency_matrix = self.get_adjacency_matrix()
        aim_adjacency_matrix = self.plan_adjacencyMatDict[self.graph['time']]
        for i in range(len(self.nodes)):
            for j in range(i):
                # break old link
                if origin_adjacency_matrix[i,j]-aim_adjacency_matrix[i,j] == 1:
                    self.remove_edge(i,j)
                # connect new link
                elif aim_adjacency_matrix[i,j]-origin_adjacency_matrix[i,j] == 1:
                    self.add_edges_from([(i,j,{'weight':self.plan_weightMatDict[self.graph['time']][i,j],
                                               'capacity_band':self.plan_linkResourceDict[self.graph['time'],'band'][i,j],
                                               'remain_band':self.plan_linkResourceDict[self.graph['time'],'band'][i,j]})])


class ServiceTopo():
    def __init__(self,idList:list[int],lifeTimeDict:dict[int:[float,float]],endPointDict:dict[int:list[int,int]],
                 arriveFunParamDict:dict[int:list],vnfRequstDict:dict[int:list],qosRequesDict:dict[int:list]):
        """_summary_

        Args:
            idList (list[int]): [id]
            lifeTimeDict (dict[int:[float,float]]): {id:[begintime,endtime]}
            endPointDict (dict[int:list[int,int]]): {id:[starpoint,endpoint]}
            arriveFunParamDict (dict[int:list]): {id:[param1,param2]}
            vnfRequstDict (dict[int:list]): {id:[vnf's type]}
            qosRequesDict (dict[int:list]): {id:[vnf's qos]}
        """

        self.plan_sfcId = idList
        self.plan_lifeTimeDict = lifeTimeDict
        self.plan_beginTimeList = [lifeTimeDict[i][0] for i in idList]
        self.plan_endTimeList = [lifeTimeDict[i][1] for i in idList]
        self.plan_endPointDict = endPointDict
        self.plan_arriveFunParam = arriveFunParamDict
        self.plan_vnfRequstDict = vnfRequstDict
        self.plan_qosRequesDict = qosRequesDict

        self.plan_sfcGraph:dict[int:Topo] = {}
        for sfcid in self.plan_sfcId:
            vnfnum = len(self.plan_vnfRequstDict[sfcid])
            G = nx.path_graph(vnfnum)
            vnftopo = Topo()
            vnftopo.__dict__['_node'] = G.__dict__['_node']
            vnftopo.__dict__['_adj'] = G.__dict__['_adj']

            for node_id in range(vnfnum):
                vnftopo.nodes[node_id]["request_cpu"] = 0
                vnftopo.nodes[node_id]["request_ram"] = 0

            for edge_temp in vnftopo.edges:
                vnftopo.edges[edge_temp]["request_band"] = 0

            self.plan_sfcGraph[sfcid] = vnftopo
            


    


