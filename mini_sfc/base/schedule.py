#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   schedule.py
@Time    :   2024/01/11 21:52:57
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from typing import Any
from data import Config
from data import SubstrateNetwork
from data import ServiceGroup
from data import ServiceChain

class Schedule:
    def __init__(self,config:Config,substrate_network:SubstrateNetwork,service_group:ServiceGroup) -> None:
        self.config = config
        self.substrate_network = substrate_network
        self.service_group = service_group
        self.events = []

        self.__generate_event_list()


    def __generate_event_list(self):
        
        topo_mode = self.substrate_network.topology_change_setting.get("type","static")
        if topo_mode == "static":
            event_list = self.__generate_sfc_event_list()
        else:
            event_list = self.__generate_sfc_event_list()
            event_list = sorted(event_list, key=lambda e: e.__getitem__('time'))
            event_list = event_list + self.__generate_topo_event_list(event_list[0]['time'],event_list[-1]['time'])

        self.events = sorted(event_list, key=lambda e: e.__getitem__('time'))
        for i, event in enumerate(self.events): 
            event['id'] = i

    def __generate_sfc_event_list(self):
        arrive_event_list = [{'sfc_id':int(service_chain.id), 'time':float(service_chain.arrivetime), 'type':1} for service_chain in self.service_group]
        end_event_list = [{'sfc_id':int(service_chain.id), 'time':float(service_chain.endtime), 'type':0} for service_chain in self.service_group]
        return arrive_event_list + end_event_list
    
    def __generate_topo_event_list(self, starttime:float, endtime:float):
        change_times = self.substrate_network.topology_change_setting["change_times"]
        change_interval = (endtime-starttime)/(change_times+1)
        topo_event_list = [{'time':float((i+1)*change_interval+starttime),'type':2} for i in range(change_times)]
        return topo_event_list
    
    