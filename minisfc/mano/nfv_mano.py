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

from minisfc.mano import NfvOrchestrator, NfvVim

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from minisfc.net import MiniContainternet
    from minisfc.solver import Solver
    from minisfc.mano import NfvManager
    from minisfc.topo import SubstrateTopo
    from minisfc.event import Event

class NfvMano:
    def __init__(self,nfvManage:'NfvManager',sfcSolver:'Solver'):
        self.nfvManage = nfvManage
        self.nfvVim = NfvVim()
        self.sfcSolver = sfcSolver

        self.nfvOrchestrator = NfvOrchestrator(nfvManage=self.nfvManage,nfvVim=self.nfvVim,sfcSolver=self.sfcSolver)
        
    
    def ready(self,substrateTopo:'SubstrateTopo',container_net:'MiniContainternet'):
        self.substrateTopo = substrateTopo
        self.container_net = container_net

        self.nfvVim.ready(substrateTopo,container_net)
        self.nfvOrchestrator.ready(substrateTopo)

    def handle(self,event:'Event'):
        # Send the event to MANO for processing, and update the substrate network according to the processing results 
        self.substrateTopo = self.nfvOrchestrator.handle(event)

    def ending(self):
        pass
        
