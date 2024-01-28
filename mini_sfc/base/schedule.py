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

from data import Config
from data import SubstrateNetwork
from data import ServiceGroup
from data import ServiceChain
from base import EventType, Event
from typing import Tuple
import copy
import code
import pickle

class Schedule:
    def __init__(self,config:Config,substrate_network:SubstrateNetwork,service_group:ServiceGroup) -> None:
        self.config = config
        self.substrate_network = substrate_network
        self.service_group = service_group
        self.events: list[Event] = []
        self.current_event_id = 0

        self.__generate_event_list()
    
    def reset(self):
        self.current_event_id = 0

    def step(self) -> Tuple[Event,bool]:
        if self.current_event_id == len(self.events):
            return None, True
        else:
            event = self.events[self.current_event_id]
            if event.type == EventType.TOPO_CHANGE:
                self.substrate_network.change_topology()
            event.current_substrate = copy.deepcopy(self.substrate_network)
            self.current_event_id += 1
            return event, False
    
    @staticmethod
    def save(schedule_obj: object,path_file: str):
        with open(path_file, "wb") as file:
            pickle.dump(schedule_obj, file)
    
    @staticmethod
    def load(path_file: str) -> object:
        with open(path_file, "rb") as file:
            loaded_data = pickle.load(file)
        return loaded_data

    def __generate_event_list(self):
        topo_mode = self.substrate_network.topology_change_setting.get("type","static")
        if topo_mode == "static":
            event_list = self.__generate_sfc_event_list()
        else:
            event_list = self.__generate_sfc_event_list()
            event_list = sorted(event_list, key=lambda e: e.time)
            event_list = event_list + self.__generate_topo_event_list(event_list[0].time,event_list[-1].time)

        self.events = sorted(event_list, key=lambda e: e.time)
        for i, event in enumerate(self.events):
            event.id = i

    def __generate_sfc_event_list(self) -> list[Event]:
        arrive_event_list = [Event(**{'type':EventType.SFC_ARRIVE,
                                      'time':float(service_chain.arrivetime),
                                      'sfc':service_chain})
                                      for service_chain in self.service_group]
        end_event_list = [Event(**{'type':EventType.SFC_ENDING,
                                   'time':float(service_chain.endtime),
                                   'sfc':service_chain})
                                   for service_chain in self.service_group]
        return arrive_event_list + end_event_list
    
    def __generate_topo_event_list(self, starttime:float, endtime:float) -> list[Event]:
        change_times = self.substrate_network.topology_change_setting["change_times"]
        change_interval = (endtime-starttime)/(change_times+1)
        topo_event_list = [Event(**{'type':EventType.TOPO_CHANGE,
                                    'time':float((i+1)*change_interval+starttime)})
                                    for i in range(change_times)]
        return topo_event_list
    
    