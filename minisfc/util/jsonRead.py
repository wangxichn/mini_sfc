#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   jsonRead.py
@Time    :   2024/06/26 09:26:28
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

import os
import numpy as np
import json

class JsonReader:
    def __init__(self,filename:str) -> None:
        self.filename = filename

        data = []
        with open(filename,'r') as file:
            data = json.load(file)

        assert data != [], ValueError(f"Data read error from {filename}")

        self.sat_name_list,self.base_name_list,self.uav_name_list = [],[],[]
        self.DATA_DIC = {}
        for data_item in data:
            node_1_name = data_item['node1']
            node_1_type = node_1_name.split('_')[0]
            if node_1_type == "SAT":
                self.sat_name_list.append(node_1_name)
            elif node_1_type == "BASE":
                self.base_name_list.append(node_1_name)
            elif node_1_type == "UAV":
                self.uav_name_list.append(node_1_name)

            node_2_name = data_item['node2']
            node_2_type = node_2_name.split('_')[0]
            if node_2_type == "SAT":
                self.sat_name_list.append(node_2_name)
            elif node_2_type == "BASE":
                self.base_name_list.append(node_2_name)
            elif node_2_type == "UAV":
                self.uav_name_list.append(node_2_name)

            self.DATA_DIC[node_1_name,node_2_name] = data_item['range']

        # 获取各类型节点的名称列表及其个数
        self.sat_name_list = sorted(list(set(self.sat_name_list)))
        plane_index,sat_index = [],[]
        for sat_item in self.sat_name_list:
            now_plane_num = int(sat_item.split('_')[1].split('-')[0])
            now_sat_num = int(sat_item.split('_')[1].split('-')[1])
            plane_index.append(now_plane_num)
            sat_index.append(now_sat_num)
        numOrbitPlanes = max(plane_index)+1
        numSatsPerPlane = max(sat_index)+1
        self.sat_name_list = []
        for i in range(numOrbitPlanes):
            for j in range(numSatsPerPlane):
                self.sat_name_list.append(f'SAT_{i}-{j}')
        self.sat_name_list = sorted(list(set(self.sat_name_list)))
        self.sat_num = numOrbitPlanes*numSatsPerPlane

        self.base_name_list = sorted(list(set(self.base_name_list)))
        self.base_num = len(self.base_name_list)

        self.uav_name_list = sorted(list(set(self.uav_name_list)))
        self.uav_num = len(self.uav_name_list)

        self.all_node_list = self.sat_name_list + self.base_name_list + self.uav_name_list

        self.NODE_INDEX_DIC = {}
        for index, node_name in enumerate(self.all_node_list):
            self.NODE_INDEX_DIC[node_name] = index
    
    def getAdjacencyMat(self):
        adjacency_mat = np.eye(len(self.all_node_list))
        for node_1_name in self.all_node_list:
            for node_2_name in self.all_node_list:
                perf_Range = self.DATA_DIC.get((node_1_name,node_2_name),None)
                if perf_Range != None:
                    adjacency_mat[self.NODE_INDEX_DIC[node_1_name],self.NODE_INDEX_DIC[node_2_name]] = 1
                    adjacency_mat[self.NODE_INDEX_DIC[node_2_name],self.NODE_INDEX_DIC[node_1_name]] = 1
        
        return adjacency_mat
    
    def getWeightMat(self):
        weight_mat = np.zeros((len(self.all_node_list),len(self.all_node_list)))
        for node_1_name in self.all_node_list:
            for node_2_name in self.all_node_list:
                perf_Range = self.DATA_DIC.get((node_1_name,node_2_name),None)
                if perf_Range != None:
                    weight_mat[self.NODE_INDEX_DIC[node_1_name],self.NODE_INDEX_DIC[node_2_name]] = perf_Range/300000
                    weight_mat[self.NODE_INDEX_DIC[node_2_name],self.NODE_INDEX_DIC[node_1_name]] = perf_Range/300000
        
        return weight_mat

    @staticmethod
    def getJsonFiles():
        directory = os.getcwd()
        files = os.listdir(directory)
        file_name_list = [file_name for file_name in files if file_name[-5:]=='.json' ]
        return file_name_list
        


