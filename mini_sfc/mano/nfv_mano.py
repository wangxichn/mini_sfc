#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   nfv_mano.py
@Time    :   2024/01/11 21:53:57
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from data import Config
from data import SubstrateNetwork
from data import ServiceChain
from mano import NfvOrchestrator
from base import EventType, Event

import logging

class NfvMano:
    def __init__(self,config:Config):
        self.config = config

        self.solver_name: str = self.config.mano_setting.get("solver_name","random")
        self.nfv_orchestrator_setting = {"solver_name":self.solver_name}
        self.nfv_orchestrator = NfvOrchestrator(**self.nfv_orchestrator_setting)


    def ready(self,substrate_network:SubstrateNetwork):
        logging.info("Nfv Mano is initializing")
        self.substrate_network = substrate_network
        self.nfv_orchestrator.ready(substrate_network)

    
    def handle(self,event:Event):
        self.nfv_orchestrator.handle(event)


