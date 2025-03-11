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

from minisfc.mano import NfvManager, NfvOrchestrator
from minisfc.topo import SubstrateTopo
from minisfc.solver import Solver
from minisfc.event import Event

class NfvMano:
    def __init__(self,nfvManage:NfvManager,sfcSolver:Solver):
        self.sfcSolver = sfcSolver
        self.nfvManage = nfvManage
        self.nfvOrchestrator = NfvOrchestrator(nfvManage,sfcSolver)
    
    def ready(self,substrateTopo:SubstrateTopo):
        self.substrateTopo = substrateTopo
        self.nfvOrchestrator.ready(substrateTopo)

    def handle(self,event:Event):
        # Send the event to MANO for processing, and update the substrate network according to the processing results 
        self.substrateTopo = self.nfvOrchestrator.handle(event)

    def ending(self):
        pass
        
