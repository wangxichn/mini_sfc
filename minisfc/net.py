#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   net.py
@Time    :   2024/06/18 16:39:32
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

import tqdm
import copy
import matplotlib.pyplot as plt
import networkx as nx
from .topo import SubstrateTopo, ServiceTopo
from .mano import NfvManager, NfvMano
from .solver import Solver
from .event import Schedule
from .trace import TRACER

class Minisfc:
    def __init__(self,substrateTopo:SubstrateTopo,serviceTopo:ServiceTopo,
                 nfvManager:NfvManager,sfcSolver:Solver):

        self.schedule = Schedule(substrateTopo,serviceTopo)
        self.nfvMano = NfvMano(nfvManager,sfcSolver)

    def ready(self):
        TRACER.ready()
        self.nfvMano.ready(copy.deepcopy(self.schedule.substrateTopo))

    def start(self):
        self.ready()

        pbar = tqdm.tqdm(desc=f'INFO:Minisfc is running with {self.nfvMano.sfcSolver.__class__.__name__}.', 
                         total=len(self.schedule.events))
        while True: # loop with event list
            event, done = self.schedule.step()

            if done == True: # all events are processed 
                break

            pbar.update(1)
            pbar.set_postfix({
                'event_id': f'{event.id}',
                'event_type': f'{event.type}',
            })

            self.nfvMano.handle(copy.deepcopy(event))
            self.update()
        
        pbar.close()

    def update(self):
        self.schedule.substrateTopo = copy.deepcopy(self.nfvMano.substrateTopo)

    def stop(self):
        pass
