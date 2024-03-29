#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   subenv.py
@Time    :   2024/03/26 16:33:35
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

import numpy as np
from data import SubstrateNetwork,ServiceChain
from base import Event,EventType
from .subsolution import SubSolution
import networkx as nx

class SubEnv():
    def __init__(self,event:Event) -> None:
        self.p_net = event.current_substrate
        self.v_net = event.sfc
        self.time = event.time
        self.curr_v_node_id = 0
        self.subsolution = SubSolution()

    def get_observation(self):
        """_summary_

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
        node_data.append(self.p_net.get_all_nodes_attrs_values("cpu_setting","remain_setting"))      #0
        node_data.append(self.p_net.get_all_nodes_attrs_values("cpu_setting","max_setting"))         #1
        node_data.append(self.p_net.get_all_nodes_attrs_values("ram_setting","remain_setting"))      #2
        node_data.append(self.p_net.get_all_nodes_attrs_values("ram_setting","max_setting"))         #3
        node_data.append(self.p_net.get_all_nodes_attrs_values("disk_setting","remain_setting"))     #4
        node_data.append(self.p_net.get_all_nodes_attrs_values("disk_setting","max_setting"))        #5
        node_data.append(self.p_net.get_all_nodes_attrs_values("energy_setting","remain_setting"))   #6
        node_data.append(self.p_net.get_all_nodes_attrs_values("energy_setting","max_setting"))      #7

        node_data.append(self.p_net.get_all_nodes_aggrlinks_attrs_values("band_setting","remain_setting")) #8
        node_data.append(self.p_net.get_all_nodes_aggrlinks_attrs_values("band_setting","max_setting"))    #9

        node_data = np.array(node_data, dtype=np.float32).T
        node_data[:,0:6]/=20
        node_data[:,6:10]/=200

        edge_data = np.array(list(self.p_net.edges)).T

        return node_data,edge_data

    def __get_v_net_obs(self):
        node_data = []
        node_data.append(self.v_net.get_all_nodes_attrs_values("cpu_setting"))   #0
        node_data.append(self.v_net.get_all_nodes_attrs_values("ram_setting"))   #1
        node_data.append(self.v_net.get_all_nodes_attrs_values("disk_setting"))  #2
        node_data.append(self.v_net.get_all_nodes_attrs_values("cpu_setting"))   #3 eng

        node_data.append(self.v_net.get_all_nodes_aggrlinks_attrs_values("band_setting"))  #4

        node_data = np.array(node_data, dtype=np.float32).T
        node_data[:,0:3]/=20
        node_data[:,3]*=(self.v_net.endtime-self.time) # change CPU to ENG
        node_data[:,3:5]/=200

        return node_data
    
    def get_action_mask(self):
        
        v_node_rq_cpu = self.v_net.get_node_attrs_value(self.curr_v_node_id,"cpu_setting")
        v_node_rq_ram = self.v_net.get_node_attrs_value(self.curr_v_node_id,"ram_setting")
        v_node_rq_disk = self.v_net.get_node_attrs_value(self.curr_v_node_id,"disk_setting")
        v_node_rq_eng = v_node_rq_cpu*(self.v_net.endtime-self.time)

        candidate_nodes = self.p_net.get_node_candidates_list(v_node_rq_cpu,v_node_rq_ram,v_node_rq_disk,v_node_rq_eng)

        mask = np.zeros(self.p_net.num_nodes, dtype=bool)
        mask[candidate_nodes] = True

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

        if self.subsolution.try_times > 10 * self.v_net.num_nodes:
            return self.__reject()

        assert action in list(self.p_net.nodes)
        check_result = self.__check_action(action)

        if not check_result:
            done = False
            return self.get_observation(), self.__compute_reward(self.subsolution), done, self.subsolution
        else:
            done = False
            self.__do_action(action)
            self.subsolution.selected_actions.append(action)
            self.curr_v_node_id += 1

            if self.curr_v_node_id >= self.v_net.num_nodes:
                done = True
                return self.get_observation(), self.__compute_reward(self.subsolution), done, self.subsolution

            return self.get_observation(), self.__compute_reward(self.subsolution), done, self.subsolution

    def __reject(self):
        self.subsolution.rejection = True
        self.subsolution.result = False
        done = True
        return self.get_observation(), self.__compute_reward(self.subsolution), done, self.subsolution

    def __compute_reward(self, solution:SubSolution) -> float:
        """Calculate deserved reward according to the result of current solution

        Args:
            solution (SubSolution)

        Returns:
            float: reward
        """
        if solution.result :
            reward = 1
        elif solution.place_result and solution.route_result:
            reward = 1 / self.v_net.num_nodes
        else:
            reward = - 1 / self.v_net.num_nodes
        self.subsolution.reward += reward
        return reward
    
    def __check_action(self, action:int):
        # check node
        v_node_rq_cpu = self.v_net.get_node_attrs_value(self.curr_v_node_id,"cpu_setting")
        v_node_rq_ram = self.v_net.get_node_attrs_value(self.curr_v_node_id,"ram_setting")
        v_node_rq_disk = self.v_net.get_node_attrs_value(self.curr_v_node_id,"disk_setting")
        v_node_rq_eng = v_node_rq_cpu*(self.v_net.endtime-self.time)

        p_node_rm_cpu = self.p_net.get_node_attrs_value(action,"cpu_setting","remain_setting")
        p_node_rm_ram = self.p_net.get_node_attrs_value(action,"ram_setting","remain_setting")
        p_node_rm_disk = self.p_net.get_node_attrs_value(action,"disk_setting","remain_setting")
        p_node_rm_eng = self.p_net.get_node_attrs_value(action,"energy_setting","remain_setting")

        node_check_flag = [v_node_rq_cpu <= p_node_rm_cpu , v_node_rq_ram <= p_node_rm_ram , 
                           v_node_rq_disk<=p_node_rm_disk , v_node_rq_eng <= p_node_rm_eng]
        if False in node_check_flag:
            self.subsolution.place_result = False
            self.subsolution.result = False
            return False
        else:
            self.subsolution.place_result = True

        # check route
        if len(self.subsolution.selected_actions) >= 1:
            last_action = self.subsolution.selected_actions[-1]
            v_link_rq_band = self.v_net.get_link_attrs_value((self.curr_v_node_id-1,self.curr_v_node_id),"band_setting")

            map_path = nx.dijkstra_path(self.p_net,last_action,action)
            if len(map_path) == 1: 
                map_link = [(map_path[0],map_path[0])]
            else:
                map_link = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]

            p_link_rm_band = [self.p_net.get_link_attrs_value((link[0],link[1]),"band_setting","remain_setting") for link in map_link]

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
        
    def __do_action(self,action):
        # embed node
        v_node_rq_cpu = self.v_net.get_node_attrs_value(self.curr_v_node_id,"cpu_setting")
        v_node_rq_ram = self.v_net.get_node_attrs_value(self.curr_v_node_id,"ram_setting")
        v_node_rq_disk = self.v_net.get_node_attrs_value(self.curr_v_node_id,"disk_setting")
        v_node_rq_eng = v_node_rq_cpu*(self.v_net.endtime-self.time)

        p_node_rm_cpu = self.p_net.get_node_attrs_value(action,"cpu_setting","remain_setting")
        p_node_rm_ram = self.p_net.get_node_attrs_value(action,"ram_setting","remain_setting")
        p_node_rm_disk = self.p_net.get_node_attrs_value(action,"disk_setting","remain_setting")
        p_node_rm_eng = self.p_net.get_node_attrs_value(action,"energy_setting","remain_setting")

        self.p_net.set_node_attrs_value(action,"cpu_setting"    ,"remain_setting",p_node_rm_cpu-v_node_rq_cpu)
        self.p_net.set_node_attrs_value(action,"ram_setting"    ,"remain_setting",p_node_rm_ram-v_node_rq_ram)
        self.p_net.set_node_attrs_value(action,"disk_setting"   ,"remain_setting",p_node_rm_disk-v_node_rq_disk)
        self.p_net.set_node_attrs_value(action,"energy_setting" ,"remain_setting",p_node_rm_eng-v_node_rq_eng)

        # embed link
        if len(self.subsolution.selected_actions) >= 1:

            last_action = self.subsolution.selected_actions[-1]
            v_link_rq_band = self.v_net.get_link_attrs_value((self.curr_v_node_id-1,self.curr_v_node_id),"band_setting")

            map_path = nx.dijkstra_path(self.p_net,last_action,action)
            if len(map_path) == 1: 
                map_link = [(map_path[0],map_path[0])]
            else:
                map_link = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]

            p_link_rm_band = [self.p_net.get_link_attrs_value((link[0],link[1]),"band_setting","remain_setting") for link in map_link]

            for i in range(len(p_link_rm_band)):
                self.p_net.set_link_attrs_value(map_link[i],"band_setting","remain_setting",p_link_rm_band[i]-v_link_rq_band)

        else:
            pass





        

