#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   event.py
@Time    :   2024/06/18 15:57:24
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

import copy
from enum import Enum, auto
from typing import Tuple
from minisfc.topo import SubstrateTopo, ServiceTopo

class EventType(Enum):
    NOTHING = auto()
    SFC_ARRIVE = auto()
    SFC_ENDING = auto()
    TOPO_CHANGE = auto()

class Event():
    def __init__(self,**kwargs) -> None:
        self.id:int = kwargs.get("id",None)
        self.type:EventType = kwargs.get("type",EventType.NOTHING)
        self.time:float = kwargs.get("time",None)

        self.substrateTopo:SubstrateTopo = kwargs.get("SubstrateTopo",None)
        self.serviceTopo:ServiceTopo = kwargs.get("ServiceTopo",None)
        self.serviceTopoId:int = kwargs.get("ServiceTopoId",None)

class Schedule():
    def __init__(self,substrateTopo:SubstrateTopo,serviceTopo:ServiceTopo):
        self.substrateTopo = substrateTopo
        self.serviceTopo = serviceTopo

        self.events: list[Event] = []
        self.current_event_id = 0

        self.__generate_event_list()

    def step(self) -> Tuple[Event,bool]:
        if self.current_event_id == len(self.events):
            return None, True
        else:
            event = self.events[self.current_event_id]
            if event.type == EventType.TOPO_CHANGE:
                self.substrateTopo.changeTopo(event.time)
            event.substrateTopo = copy.deepcopy(self.substrateTopo)
            self.current_event_id += 1
            return event, False

    def __generate_event_list(self):
        event_list = self.__generate_sfc_event_list() + self.__generate_topo_event_list()
        self.events = sorted(event_list, key=lambda e: e.time)
        for i, event in enumerate(self.events):
            event.id = i

    def __generate_sfc_event_list(self) -> list[Event]:
        arrive_event_list = [Event(**{'type':EventType.SFC_ARRIVE,
                                      'time':beginTime,
                                      'ServiceTopo':self.serviceTopo,
                                      'ServiceTopoId':self.serviceTopo.plan_sfcId[i]})
                                      for i,beginTime in enumerate(self.serviceTopo.plan_beginTimeList)]
        end_event_list = [Event(**{'type':EventType.SFC_ENDING,
                                   'time':endTime,
                                   'ServiceTopo':self.serviceTopo,
                                   'ServiceTopoId':self.serviceTopo.plan_sfcId[i]})
                                   for i,endTime in enumerate(self.serviceTopo.plan_endTimeList)]
        return arrive_event_list + end_event_list
    
    def __generate_topo_event_list(self) -> list[Event]:
        topo_event_list = [Event(**{'type':EventType.TOPO_CHANGE,
                                    'time':changeTime,
                                    'ServiceTopo':self.serviceTopo})
                                    for changeTime in self.substrateTopo.plan_changeTimeList]
        return topo_event_list