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

from mininet.net import Containernet
from mininet.node import Controller, RemoteController, Switch
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel

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
        # ----------------------------------
        self.useContainter = useContainter
        self.useRemoteController = False


    def ready(self):
        TRACER.ready()

        if self.useContainter:
            setLogLevel('info')
            self.containerNet = Containernet(controller=Controller)

            if not self.useRemoteController:
                self.containerNet.addController('c0')

            swicthes: dict[int, Switch] = {}
            for node_temp in list(self.schedule.substrateTopo.nodes):
                temple_switch = self.containerNet.addSwitch(f's{node_temp}')
                swicthes[node_temp] = temple_switch

            for edge_temp in self.schedule.substrateTopo.edges:
                if edge_temp[0] == edge_temp[1]:
                    continue
                self.containerNet.addLink(swicthes[edge_temp[0]], swicthes[edge_temp[1]], cls=TCLink, 
                                            delay=f"{self.schedule.substrateTopo.edges[edge_temp]['weight']}ms", 
                                            bw=self.schedule.substrateTopo.edges[edge_temp]['capacity_band'])
                
        self.nfvMano.ready(copy.deepcopy(self.schedule.substrateTopo))


    def start(self):
        self.ready()

        if self.useContainter:
            self.containerNet.start()

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
        if self.useContainter:
            self.containerNet.stop()

    def addCLI(self):
        if not self.useContainter:
            print('WARNING: addCLI() is only available when useContainter is True.')
            return

        CLI(self.containerNet)

    def addRemoteController(self,name='c0', ip='127.0.0.1', port=6653):
        if not self.useContainter:
            print('WARNING: addRemoteController() is only available when useContainter is True.')
            return
        
        self.useRemoteController = True
        self.containerNet.addController(name=name, controller=RemoteController, ip=ip, port=port)
