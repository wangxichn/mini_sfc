#Anaconda/envs/pyqtenv python
# -*- coding: utf-8 -*-
'''
ComMinisfcDataFun.py
====================

.. module:: ComMinisfcDataFun
  :platform: Windows, Linux
  :synopsis: Minisfc仿真数据分析功能组件模块

.. moduleauthor:: WangXi

简介
----


版本
----

- 版本 1.0 (2025/04/01): 初始版本

'''

import networkx as nx
import numpy as np
import pandas as pd
import os
import logging
import pickle

from PyQt5.QtCore import pyqtSlot, pyqtSignal

from Netterminal.Sources.Component.ComBaseFun import ComBaseFun
from Netterminal.Sources.Device.DevFileSelector import DevFileSelector

class ComMinisfcDataFun(ComBaseFun):
    data_ready_signal = pyqtSignal()
    def __init__(self, name:str, **kwargs):
        super(ComMinisfcDataFun,self).__init__(name)

        self.register(**kwargs)
        self.ready()
        
        self.node_pos = None
        self.current_adjmatrix = None
        self.data_ready_to_play = False

    def register(self, **kwargs):
        self.devFileSelector = DevFileSelector("FileSelector",**kwargs)
        
    def ready(self):
        self.devFileSelector.ready()
        self.devFileSelector.file_choosed_signal.connect(self.ctl_get_simulation_data)
        
    def ctl_get_simulation_data(self):
        self.data_ready_to_play = False
        if not os.path.exists(self.devFileSelector.file_path):
            logging.error(f"file {self.devFileSelector.file_path} not exist")
            return
        
        self.simulation_data_file = self.devFileSelector.file_path
        self.simulation_df = pd.read_csv(self.simulation_data_file)
        self.simulation_timeseries = self.simulation_df['Time'].values
        self.simulation_substrateTopo = self._ctl_get_simulation_topo()
        self.simulation_data_nodes_load = {}
        for time in self.simulation_timeseries:
            cpu_usage_rate_list, ram_usage_rate_list = self.ctl_get_simulation_nodes_load(time)
            self.simulation_data_nodes_load[time] = {"cpu":cpu_usage_rate_list, "ram":ram_usage_rate_list}
        
        self.data_ready_signal.emit()
        
        
    def _ctl_get_simulation_topo(self):
        simulation_id = self.simulation_data_file.split('_')[-1].split(".")[0]
        simulation_topo_file = os.path.join(os.path.dirname(self.simulation_data_file),f"SubstrateTopo_{simulation_id}.pkl")
        if not os.path.exists(simulation_topo_file):
            logging.error(f"file {self.devFileSelector.file_path} not exist")
            return
        with open(simulation_topo_file, "rb") as file:
            simulation_substrateTopo: SubstrateTopo = pickle.load(file)
        return simulation_substrateTopo
    
    def ctl_get_simulation_nodes_load(self,time):
        if time not in self.simulation_timeseries:
            logging.error(f"time {time} not exist in simulation data")
            return
        
        cpu_usage_rate_list = []
        ram_usage_rate_list = []
        for i in range(len(self.simulation_substrateTopo.nodes)):
            cpu_key = f'NVFI_{i}_cpu'
            ram_key = f'NVFI_{i}_ram'
            
            total_cpu = self.simulation_df[cpu_key].iloc[0]
            total_ram = self.simulation_df[ram_key].iloc[0]
            
            index = np.where(self.simulation_timeseries == time)[0][0]
            
            cpu_usage_rate = (total_cpu - self.simulation_df[cpu_key].iloc[index]) / total_cpu
            ram_usage_rate = (total_ram - self.simulation_df[ram_key].iloc[index]) / total_ram
            
            cpu_usage_rate_list.append(cpu_usage_rate)
            ram_usage_rate_list.append(ram_usage_rate)
        
        return cpu_usage_rate_list, ram_usage_rate_list
    
    def ctl_get_nodes_load_colors(self, time, resourse_type:str):
        if time not in self.simulation_timeseries:
            logging.error(f"time {time} not exist in simulation data")
            return
        
        if resourse_type == "cpu":
            nodes_load = self.simulation_data_nodes_load[time]["cpu"]
            return self.ctl_load_to_rgb(nodes_load)
        elif resourse_type == "ram":
            nodes_load = self.simulation_data_nodes_load[time]["ram"]
            return self.ctl_load_to_rgb(nodes_load)
        else:
            logging.error(f"resourse_type {resourse_type} not support")
    
    def ctl_load_to_rgb(self, load_values:list[float]) -> list[list[float]]:
        """
        将资源负载值(0-1范围的小数)映射为RGB颜色值。
        
        参数:
            load_values (list or np.ndarray): 一个包含0到1之间小数的向量,表示资源负载。
            
        返回:
            np.ndarray: 一个形状为 (n, 3) 的数组,每一行是一个RGB颜色值(范围在0-255之间)。
        """
        load_values = np.array(load_values)
        if not np.all((load_values >= 0) & (load_values <= 1)):
            raise ValueError("ctl_load_to_rgb函数的所有输入负载值必须在0到1之间")
        
        # 定义颜色映射：从蓝色（低负载）到红色（高负载），使用非线性过渡
        def interpolate_color(value):
            # 非线性调整：让红色更容易出现
            adjusted_value = value ** 0.5  # 平方根函数加速红色的出现
            
            if adjusted_value < 0.25:
                # 从深蓝色到浅蓝色过渡
                r = int(64 * (adjusted_value / 0.25))  # 增加一点柔和的红
                g = int(64 * (adjusted_value / 0.25))  # 增加一点柔和的绿
                b = 128 + int(127 * (adjusted_value / 0.25))  # 蓝色为主
            elif adjusted_value < 0.5:
                # 从浅蓝色到浅绿色过渡
                r = int(64 * (1 - (adjusted_value - 0.25) / 0.25))
                g = 128 + int(127 * ((adjusted_value - 0.25) / 0.25))
                b = 255 - int(127 * ((adjusted_value - 0.25) / 0.25))
            elif adjusted_value < 0.75:
                # 从浅绿色到橙色过渡
                r = 128 + int(127 * ((adjusted_value - 0.5) / 0.25))
                g = 255 - int(127 * ((adjusted_value - 0.5) / 0.25))
                b = 0
            else:
                # 从橙色到柔和的红色过渡
                r = 255
                g = int(64 * (1 - (adjusted_value - 0.75) / 0.25))  # 减少绿色，保持柔和
                b = 0
            
            return [r/255, g/255, b/255]
        
        # 对每个负载值计算对应的 RGB 值
        rgb_colors = np.array([interpolate_color(value) for value in load_values])
        
        return rgb_colors
        
        

# region topo.py
# 以下程序来源于MiniSFC项目中的topo.py文件，用于读取仿真记录文件中的拓扑信息 ----------------------------

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
                 vnfRequstDict:dict[int:list],qosRequesDict:dict[int:list],arriveFunParamDict:dict[int:list]=None):
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
            
# endregion topo.py

    



        


        


