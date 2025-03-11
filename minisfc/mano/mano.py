#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   nfv_mano.py
@Time    :   2024/06/18 17:51:03
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from minisfc.mano.nfvo import NfvOrchestrator
from minisfc.mano.vim import NfvVim

from mininet.net import Containernet
from minisfc.solver import Solver
from minisfc.mano.vnfm import VnfManager
from minisfc.topo import SubstrateTopo
from minisfc.event import Event

import copy

class NfvMano:
    def __init__(self,vnfManager:VnfManager,sfcSolver:Solver):
        self.vnfManager = vnfManager
        self.nfvVim = NfvVim()
        self.sfcSolver = sfcSolver

        self.nfvOrchestrator = NfvOrchestrator(vnfManager=self.vnfManager,nfvVim=self.nfvVim,sfcSolver=self.sfcSolver)
        
    
    def ready(self,substrateTopo:SubstrateTopo,container_net:Containernet):
        self.substrateTopo = copy.deepcopy(substrateTopo)
        self.container_net = container_net

        self.nfvVim.ready(self.substrateTopo,self.container_net)
        self.vnfManager.ready(self.nfvVim)
        self.nfvOrchestrator.ready()


    def handle(self,event:'Event'):
        # Send the event to MANO for processing, and update the substrate network according to the processing results 
        self.substrateTopo = self.nfvOrchestrator.handle(event)


    def ending(self):
        pass
        
