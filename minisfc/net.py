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

from mininet.net import Containernet
from mininet.node import Controller, RemoteController, Switch
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel

from minisfc.topo import SubstrateTopo, ServiceTopo
from minisfc.mano import NfvManager, NfvMano
from minisfc.solver import Solver
from minisfc.event import Schedule, Event
from minisfc.trace import TRACER

class Minisfc:
    def __init__(self,substrateTopo:SubstrateTopo,serviceTopo:ServiceTopo,
                 nfvManager:NfvManager,sfcSolver:Solver,use_container: bool = False):

        self.schedule = Schedule(substrateTopo,serviceTopo)
        self.nfvMano = NfvMano(nfvManager,sfcSolver)
        self.env = simpy.RealtimeEnvironment(factor=1) if use_container else simpy.Environment()
        # ----------------------------------

        if use_container:
            setLogLevel('info')
            self.container_net = MiniContainternet(controller=Controller)
            self.use_remote_controller = False
        else:
            self.container_net = None


    def ready(self):
        TRACER.ready()

        if self.container_net != None:
            print('INFO: Minisfc is running with containernet.')
            if not self.use_remote_controller:
                self.container_net.addController('c0')

            switch_map: dict[int, Switch] = {}
            for node_temp in list(self.schedule.substrateTopo.nodes):
                temple_switch = self.container_net.addSwitch(f's_{node_temp}')
                switch_map[node_temp] = temple_switch

            for edge_temp in self.schedule.substrateTopo.edges:
                if edge_temp[0] == edge_temp[1]:
                    continue
                self.container_net.addLink(switch_map[edge_temp[0]], switch_map[edge_temp[1]], cls=TCLink, 
                                            delay=f"{self.schedule.substrateTopo.edges[edge_temp]['weight']}ms", 
                                            bw=self.schedule.substrateTopo.edges[edge_temp]['capacity_band'])
            self.container_net.swicth_map = switch_map
                
        self.nfvMano.ready(copy.deepcopy(self.schedule.substrateTopo),self.container_net)


    def start(self):
        self.ready()

        if self.container_net != None:
            self.container_net.start()

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
        if self.container_net != None:
            self.container_net.stop()

    def addCLI(self):
        if self.container_net == None:
            print('WARNING: addCLI() is only available when use_container is True.')
            return

        CLI(self.container_net)

    def addRemoteController(self,name='c0', ip='127.0.0.1', port=6653):
        if self.container_net == None:
            print('WARNING: addRemoteController() is only available when use_container is True.')
            return
        
        self.use_remote_controller = True
        self.container_net.addController(name=name, controller=RemoteController, ip=ip, port=port)


class MiniContainternet(Containernet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.swicth_map: dict[int, Switch] = {}
