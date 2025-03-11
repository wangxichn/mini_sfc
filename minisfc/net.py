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
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel

from minisfc.topo import SubstrateTopo, ServiceTopo
from minisfc.solver import Solver
from minisfc.event import Schedule, Event
from minisfc.trace import TRACER
from minisfc.mano.vnfm import VnfManager
from minisfc.mano.mano import NfvMano

class Minisfc:
    def __init__(self,substrateTopo:SubstrateTopo,serviceTopo:ServiceTopo,
                 vnfManager:VnfManager,sfcSolver:Solver,use_container: bool = False):

        self.schedule = Schedule(substrateTopo,serviceTopo)
        self.nfvMano = NfvMano(vnfManager,sfcSolver)
        self.env: simpy.Environment = simpy.RealtimeEnvironment(factor=1) if use_container else simpy.Environment()
        # ----------------------------------

        if use_container:
            setLogLevel('info')
            self.containernet_handle = Containernet(controller=Controller)
            self.use_remote_controller = False
        else:
            self.containernet_handle = None


    def ready(self):
        TRACER.ready()

        if self.containernet_handle != None:
            print('INFO: Minisfc is running with containernet.')
            if not self.use_remote_controller:
                self.containernet_handle.addController('c0')

        self.nfvMano.ready(self.schedule.substrateTopo,self.containernet_handle)


    def start(self):
        self.ready()

        if self.containernet_handle != None:
            self.containernet_handle.start()

        pbar = tqdm.tqdm(desc=f'INFO:Minisfc is running with {self.nfvMano.sfcSolver.__class__.__name__}.',
                         total=len(self.schedule.events))

        def handle_event(env: simpy.Environment, event: Event, pbar: tqdm.tqdm):

            event_trigger_time = event.time - env.now
            yield env.timeout(event_trigger_time)

            event, _ = self.schedule.step()
            self.nfvMano.handle(copy.deepcopy(event))

            self.update()

            pbar.update(1)
            pbar.set_postfix({
                'event_time': f'{event.time:.2f}',
                'event_type': f'{event.type}',
            })

        for event in self.schedule.events:
            self.env.process(handle_event(self.env, event, pbar))

        self.env.run(until=self.schedule.events[-1].time+1)

        pbar.close()

    def update(self):
        self.schedule.substrateTopo = copy.deepcopy(self.nfvMano.substrateTopo)

    def stop(self):
        if self.containernet_handle != None:
            self.containernet_handle.stop()

    def addCLI(self):
        if self.containernet_handle == None:
            print('WARNING: addCLI() is only available when use_container is True.')
            return

        CLI(self.containernet_handle)

    def addRemoteController(self,name='c0', ip='127.0.0.1', port=6653):
        if self.containernet_handle == None:
            print('WARNING: addRemoteController() is only available when use_container is True.')
            return
        
        self.use_remote_controller = True
        self.containernet_handle.addController(name=name, controller=RemoteController, ip=ip, port=port)


