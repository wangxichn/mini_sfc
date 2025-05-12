#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   subenv.py
@Time    :   2024/06/23 16:40:01
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   Ref. https://github.com/GeminiLight/drl-sfcp
             DRL-SFCP: Adaptive Service Function Chains Placement with Deep Reinforcement Learning
             By Wang, Tianfu and Fan, Qilin and Li, Xiuhua and Zhang, Xu and Xiong, Qingyu and Fu, Shu and Gao, Min
'''

import sys
sys.path.append("..//..//")
from minisfc.topo import SubstrateTopo, ServiceTopo, Topo
from minisfc.event import Event
from minisfc.solver import Solution
import torch
from torch_geometric.data import Data, Batch
import networkx as nx
import numpy as np
from typing import Union

class SubSolution:
    def __init__(self) -> None:
        self.try_times = 0
        self.selected_actions = []
        self.result = False
        self.place_result = False
        self.route_result = False
        self.rejection = False
        self.reward = 0

class SubEnv:
    def __init__(self,event:Event,solution:Solution) -> None:
        self.p_net = event.substrateTopo
        self.v_netId = event.serviceTopoId
        self.v_nets = event.serviceTopo
        self.v_netGraph: Topo = event.serviceTopo.plan_sfcGraph[self.v_netId]
        self.solution = solution
        self.time = event.time
        self.curr_v_node_id = 0
        self.subsolution = SubSolution()

    def get_observation(self):
        """get_observation

        Args:
            event (Event)

        Returns:
            dict['p_net_x':NDArray[float32] p_net_node_num * node_features,
                 'p_net_edge':NDArray[int] 2 * edge_num
                 'v_net_x':NDArray[float32]] v_net_node_num * node_features
        """
        p_net_obs,p_net_edge = self.__get_p_net_obs()
        v_net_obs = self.__get_v_net_obs()
        
        return {'p_net_x': p_net_obs,
                'p_net_edge': p_net_edge,
                'v_net_x': v_net_obs}
    
    def __get_p_net_obs(self):
        node_data = []
        node_data.append(self.p_net.get_all_nodes_attrs_values('remain_cpu'))      #0
        node_data.append(self.p_net.get_all_nodes_attrs_values('capacity_cpu'))    #1
        node_data.append(self.p_net.get_all_nodes_attrs_values('remain_ram'))      #2
        node_data.append(self.p_net.get_all_nodes_attrs_values('capacity_ram'))    #3
        node_data.append(self.p_net.get_all_nodes_aggrlinks_attrs_values('remain_band'))    #4
        node_data.append(self.p_net.get_all_nodes_aggrlinks_attrs_values('capacity_band'))  #5
        node_data = np.array(node_data, dtype=np.float32).T

        edge_data = np.array(list(self.p_net.edges)).T

        return node_data,edge_data

    def __get_v_net_obs(self):
        node_data = []
        node_data.append(self.solution.resource['cpu'])   #0
        node_data.append(self.solution.resource['ram'])   #1
        links_band = self.solution.resource['band']
        node_aggrlinks_band = []
        for i in range(len(self.v_netGraph.nodes)):
            if i == 0:
                node_aggrlinks_band.append(links_band[i])
            elif i == (len(self.v_netGraph.nodes)-1):
                node_aggrlinks_band.append(links_band[-1])
            else:
                node_aggrlinks_band.append(links_band[i-1]+links_band[i])
        node_data.append(node_aggrlinks_band)             #2

        node_data = np.array(node_data, dtype=np.float32).T

        return node_data
    
    @staticmethod
    def v_net_obs_to_tensor(obs:Union[dict,list], device) -> dict:
        """v_net_obs_to_tensor

        Args:
            obs (dict): _description_
            device (_type_): _description_

        Returns:
            dict: {'v_net_x': obs_v_net_x}
        """
        if isinstance(obs, dict):
            v_net_x = obs['v_net_x']
            obs_v_net_x = torch.FloatTensor(v_net_x).unsqueeze(dim=0).to(device)
            return {'v_net_x': obs_v_net_x}
        elif isinstance(obs, list):
            obs_batch = obs
            v_net_x_list = []
            for observation in obs:
                v_net_x = obs['v_net_x']
                v_net_x_list.append(v_net_x)
            obs_v_net_x = torch.FloatTensor(np.array(v_net_x_list)).to(device)
            return {'v_net_x': obs_v_net_x}
        else:
            raise Exception(f"Unrecognized type of observation {type(obs)}")
    
    @staticmethod
    def p_net_obs_to_tensor(obs:Union[dict,list], device) -> dict:
        """p_net_obs_to_tensor

        Args:
            obs (dict): _description_
            device (_type_): _description_

        Returns:
            dict: { 'p_net': p_net_obs, 
                    'p_net_node': p_net_node, 
                    'hidden_state': hidden_state, 
                    'encoder_outputs': encoder_outputs}
        """
        if isinstance(obs, dict):
            p_net_x = torch.tensor(obs['p_net_x'])
            p_net_edge = torch.tensor(obs['p_net_edge']).long()
            p_net_edge_attr = None
            # Data object containing node and edge information in Pytorch Geometric format.
            data = Data(x=p_net_x, edge_index=p_net_edge, edge_attr=p_net_edge_attr)
            p_net_obs = Batch.from_data_list([data]).to(device)
            p_net_node = torch.LongTensor([obs['p_net_node']]).to(device)
            hidden_state = torch.FloatTensor(obs['hidden_state']).unsqueeze(dim=0).to(device)
            encoder_outputs = torch.FloatTensor(obs['encoder_outputs']).unsqueeze(dim=0).to(device)

            return {'p_net': p_net_obs, 'p_net_node': p_net_node, 
                    'hidden_state': hidden_state, 'encoder_outputs': encoder_outputs}
        elif isinstance(obs, list):
            obs_batch = obs
            p_net_data_list, p_net_node_list, hidden_state_list, encoder_outputs_list = [], [], [], []
            for observation in obs_batch:
                p_net_x = torch.tensor(observation['p_net_x'])
                p_net_edge = torch.tensor(observation['p_net_edge']).long()
                p_net_edge_attr = None
                # Data object containing node and edge information in Pytorch Geometric format.
                p_net_data = Data(x=p_net_x, edge_index=p_net_edge, edge_attr=p_net_edge_attr)
                p_net_node = observation['p_net_node']
                hidden_state = observation['hidden_state']
                encoder_outputs = observation['encoder_outputs']
                p_net_data_list.append(p_net_data)
                p_net_node_list.append(p_net_node)
                hidden_state_list.append(hidden_state)
                encoder_outputs_list.append(encoder_outputs)
            obs_p_net_node = torch.LongTensor(np.array(p_net_node_list)).to(device)
            obs_hidden_state = torch.FloatTensor(np.array(hidden_state_list)).to(device)
            obs_p_net = Batch.from_data_list(p_net_data_list).to(device)
            # Pad sequences with zeros and get the mask of padded elements
            sequences = encoder_outputs_list
            max_length = max([seq.shape[0] for seq in sequences])
            padded_sequences = np.zeros((len(sequences), max_length, sequences[0].shape[1]))
            mask = np.zeros((len(sequences), max_length), dtype=np.bool_)
            for i, seq in enumerate(sequences):
                seq_len = seq.shape[0]
                padded_sequences[i, :seq_len, :] = seq
                mask[i, :seq_len] = 1
            obs_encoder_outputs = torch.FloatTensor(np.array(padded_sequences)).to(device)
            obs_mask = torch.FloatTensor(mask).to(device)

            return {'p_net': obs_p_net, 'p_net_node': obs_p_net_node, 
                    'hidden_state': obs_hidden_state, 'encoder_outputs': obs_encoder_outputs}
        else:
            raise ValueError('obs type error')
    
    def get_action_mask(self):
        request_cpu = self.solution.resource['cpu'][self.curr_v_node_id]
        request_ram = self.solution.resource['ram'][self.curr_v_node_id]

        cpu_values = self.p_net.get_all_nodes_attrs_values('remain_cpu')
        ram_values = self.p_net.get_all_nodes_attrs_values('remain_ram')
        cadidate_nodes = []
        for node in self.p_net.nodes:
            if request_cpu <= cpu_values[node] and request_ram <= ram_values[node]:
                cadidate_nodes.append(node)

        mask = np.zeros(len(self.p_net.nodes), dtype=bool)
        mask[cadidate_nodes] = True

        return mask

    def step(self, action:int):
        """sub env step

        Args:
            action (int): 

        Returns:
            self.get_observation (dict): \\
            self.__compute_reward (float): \\
            done (bool): \\
            self.subsolution (object): \\ 
        """
        self.subsolution.try_times += 1

        if self.subsolution.try_times > 10 * len(self.v_netGraph.nodes):
            return self.reject()

        assert action in list(self.p_net.nodes)
        check_result = self.check_action(action)

        if not check_result:
            done = False
            return self.get_observation(), self.compute_reward(self.subsolution), done, self.subsolution
        else:
            done = False
            self.do_action(action)
            self.subsolution.selected_actions.append(action)
            self.curr_v_node_id += 1

            if self.curr_v_node_id >= len(self.v_netGraph.nodes):
                done = True
                return self.get_observation(), self.compute_reward(self.subsolution), done, self.subsolution

            return self.get_observation(), self.compute_reward(self.subsolution), done, self.subsolution

    def reject(self):
        self.subsolution.rejection = True
        self.subsolution.result = False
        done = True
        return self.get_observation(), self.compute_reward(self.subsolution), done, self.subsolution

    def compute_reward(self, subsolution:SubSolution) -> float:
        """Calculate deserved reward according to the result of current solution

        Args:
            subsolution (SubSolution)

        Returns:
            float: reward
        """
        if subsolution.result :
            reward = 1
        elif subsolution.place_result and subsolution.route_result:
            reward = 1 / len(self.v_netGraph.nodes)
        else:
            reward = - 1 / len(self.v_netGraph.nodes)
        self.subsolution.reward += reward
        return reward
    
    def check_action(self, action:int):
        # check node
        v_node_rq_cpu = self.solution.resource['cpu'][self.curr_v_node_id]
        v_node_rq_ram = self.solution.resource['ram'][self.curr_v_node_id]

        p_node_rm_cpu = self.p_net.opt_node_attrs_value(action,'remain_cpu','get')
        p_node_rm_ram = self.p_net.opt_node_attrs_value(action,'remain_ram','get')

        node_check_flag = [v_node_rq_cpu <= p_node_rm_cpu , v_node_rq_ram <= p_node_rm_ram]
        if False in node_check_flag:
            self.subsolution.place_result = False
            self.subsolution.result = False
            return False
        else:
            self.subsolution.place_result = True

        # check route
        if len(self.subsolution.selected_actions) >= 1:
            last_action = self.subsolution.selected_actions[-1]
            v_link_rq_band = self.solution.resource['band'][len(self.subsolution.selected_actions)-1]

            map_path = self.p_net.get_djikstra_path(last_action,action)
            if len(map_path) == 0:
                self.subsolution.route_result = False
                self.subsolution.result = False
                return False
            elif len(map_path) == 1: 
                map_link = [(map_path[0],map_path[0])]
            else:
                map_link = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]

            p_link_rm_band = [self.p_net.opt_link_attrs_value((link[0],link[1]),'remain_band','get') for link in map_link]

            link_check_flag = [v_link_rq_band <= band for band in p_link_rm_band]
            if False in link_check_flag:
                self.subsolution.route_result = False
                self.subsolution.result = False
                return False
            else:
                self.subsolution.route_result = True
                self.subsolution.result = True
                return True

        else:
            self.subsolution.route_result = True
            self.subsolution.result = True
            return True
        
    def do_action(self,action):
        # embed node
        v_node_rq_cpu = self.solution.resource['cpu'][self.curr_v_node_id]
        v_node_rq_ram = self.solution.resource['ram'][self.curr_v_node_id]

        self.p_net.opt_node_attrs_value(action,'remain_cpu','decrease',v_node_rq_cpu)
        self.p_net.opt_node_attrs_value(action,'remain_ram','decrease',v_node_rq_ram)

        # embed link
        if len(self.subsolution.selected_actions) >= 1:

            last_action = self.subsolution.selected_actions[-1]
            v_link_rq_band = self.solution.resource['band'][len(self.subsolution.selected_actions)-1]

            map_path = self.p_net.get_djikstra_path(last_action,action)
            if len(map_path) == 1: 
                map_link = [(map_path[0],map_path[0])]
            else:
                map_link = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]

            for link in map_link:
                self.p_net.opt_link_attrs_value(link,'remain_band','decrease',v_link_rq_band)
        else:
            pass
