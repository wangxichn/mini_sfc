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

import simpy
import tqdm
import copy
import matplotlib.pyplot as plt
import networkx as nx
from .topo import SubstrateTopo, ServiceTopo
from .mano import NfvManager, NfvMano
from .solver import Solver
from .event import Schedule, Event
from .trace import TRACER

class Minisfc:
    def __init__(self,substrateTopo:SubstrateTopo,serviceTopo:ServiceTopo,
                 nfvManager:NfvManager,sfcSolver:Solver,useContainter: bool = False):

        self.schedule = Schedule(substrateTopo,serviceTopo)
        self.nfvMano = NfvMano(nfvManager,sfcSolver)
        self.env = simpy.RealtimeEnvironment(factor=1) if useContainter else simpy.Environment()
        self.useContainter = useContainter

    def ready(self):
        TRACER.ready()
        self.nfvMano.ready(copy.deepcopy(self.schedule.substrateTopo))

    def start(self):
        self.ready()

        pbar = tqdm.tqdm(desc=f'INFO:Minisfc is running with {self.nfvMano.sfcSolver.__class__.__name__}.',
                         total=len(self.schedule.events))

        def handle_event(env, event: Event, pbar: tqdm.tqdm):

            event_trigger_time = event.time - env.now
            yield env.timeout(event_trigger_time)

            event, _ = self.schedule.step()
            self.nfvMano.handle(copy.deepcopy(event))

            self.update()

            pbar.update(1)
            pbar.set_postfix({
                'event_time': f'{event.time}',
                'event_type': f'{event.type}',
            })

        for event in self.schedule.events:
            self.env.process(handle_event(self.env, event, pbar))

        self.env.run(until=self.schedule.events[-1].time+1)

        pbar.close()

    def update(self):
        self.schedule.substrateTopo = copy.deepcopy(self.nfvMano.substrateTopo)

    def stop(self):
        pass

