#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   scenario.py
@Time    :   2024/01/11 21:50:13
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from base import Schedule
from mano import NfvMano
from data import Config
from data import SubstrateNetwork
from data import ServiceGroup

import copy
import code

class Scenario:

    def __init__(self, config:Config, schedule:Schedule, nfv_mano:NfvMano):
        self.config = config
        self.schedule = schedule
        self.nfv_mano = nfv_mano


    @classmethod
    def build(cls, config:Config):

        substrate_network = SubstrateNetwork(config)
        service_group = ServiceGroup(config)
        
        schedule = Schedule(config,substrate_network,service_group)
        nfv_mano = NfvMano(config)

        scenario = cls(config,schedule,nfv_mano)
        return scenario
        
    def start(self):
        pass
        






