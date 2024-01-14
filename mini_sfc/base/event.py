#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   event.py
@Time    :   2024/01/14 16:37:46
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from enum import Enum
from data import ServiceChain
from data import SubstrateNetwork

class EventType(Enum):
    NOTHING = 0
    SFC_ARRIVE = 1
    SFC_ENDING = 2
    TOPO_CHANGE = 3

class Event():
    def __init__(self,**kwargs) -> None:
        self.id:int = kwargs.get("id",0)
        self.type:EventType = kwargs.get("type",EventType.NOTHING)
        self.time:float = kwargs.get("time",0.0)

        if self.type == EventType.SFC_ARRIVE or self.type == EventType.SFC_ENDING:
            self.sfc_id:int = kwargs.get("sfc_id",0)
            self.sfc:ServiceChain = None
        elif self.type == EventType.TOPO_CHANGE:
            self.current_topo:SubstrateNetwork = None
        
