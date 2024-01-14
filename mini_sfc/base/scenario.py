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

import tqdm

from base import Schedule
from mano import NfvMano
from data import Config
from data import SubstrateNetwork
from data import ServiceGroup
from base.event import Event
from base.event import EventType
from typing import Union
import networkx as nx
import matplotlib.pyplot as plt


import copy
import code
import logging

class Scenario:

    def __init__(self, config:Config, schedule:Schedule, nfv_mano:NfvMano):
        self.config = config
        self.schedule = schedule
        self.nfv_mano = nfv_mano

        self.exp_repeat_time: int = self.config.scenario_setting.get("exp_repeat_time",1)
        self.solver_name = self.config.scenario_setting.get("solver_name","algorithm1")


    @classmethod
    def build(cls, config:Config):
        substrate_network = SubstrateNetwork(config)
        service_group = ServiceGroup(config)
        
        schedule = Schedule(config,substrate_network,service_group)
        nfv_mano = NfvMano(config)

        scenario = cls(config,schedule,nfv_mano)
        return scenario

    def rebuild(self):
        substrate_network = SubstrateNetwork(self.config)
        service_group = ServiceGroup(self.config)
        self.schedule = Schedule(self.config,substrate_network,service_group)
    
    def ready(self):
        pass

    def start(self):

        self.ready()

        for exp_id in range(self.exp_repeat_time):
            logging.info(f"{'*' * 10} the {exp_id} experiment is underway {'*' * 10}")

            if exp_id != 0:
                self.rebuild()

            logging.info(f"The experiment event time from {self.schedule.events[0].time} to {self.schedule.events[-1].time}")

            pbar = tqdm.tqdm(desc=f'INFO:root:Experiment with Solver {self.solver_name}', total=len(self.schedule.events))

            while True:
                event, done = self.schedule.step()

                if done == True:
                    break


                # #  Draw and save topology changes for debugging 
                # if event.type == EventType.TOPO_CHANGE:
                #     fig = plt.figure()
                #     pos = {node: event.current_topo.nodes[node]['pos'] for node in event.current_topo.nodes}
                #     nx.draw(event.current_topo,pos=pos)
                #     plt.set_loglevel("error")
                #     fig.savefig(f"{self.config.save_path}+{event.id}.png")

                pbar.update(1)
                pbar.set_postfix({
                    'event_id': f'{event.id}',
                    'event_type': f'{event.type}',
                })
            
            pbar.close()


            
            



        






