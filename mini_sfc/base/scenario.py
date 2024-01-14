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
from data import Config
from data import SubstrateNetwork
from data import ServiceGroup
from mano import NfvMano
from base import EventType, Event

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


    @classmethod
    def build(cls, config:Config):
        substrate_network = SubstrateNetwork(config)
        service_group = ServiceGroup(config)
        
        schedule = Schedule(config,substrate_network,service_group)
        nfv_mano = NfvMano(config)

        scenario = cls(config,schedule,nfv_mano)
        return scenario

    def rebuild(self):
        logging.info("The experiment scenario is rebuilding")
        substrate_network = SubstrateNetwork(self.config)
        service_group = ServiceGroup(self.config)
        self.schedule = Schedule(self.config,substrate_network,service_group)
        self.nfv_mano = NfvMano(self.config)
        
    
    def ready(self):
        pass

    def start(self):

        self.ready()

        for exp_id in range(self.exp_repeat_time):
            # ready for the new experiment
            logging.info(f"The {exp_id}-th experiment is underway")
            if exp_id != 0: self.rebuild()
            self.nfv_mano.ready(copy.deepcopy(self.schedule.substrate_network))
            # pbar = tqdm.tqdm(desc=f'INFO:root:Experiment with Solver {self.nfv_mano.solver_name}', total=len(self.schedule.events))

            # loop with event list
            while True:
                event, done = self.schedule.step()

                if done == True:
                    # all events are processed 
                    break

                # do something for dubug the scenaria and show information ---------------------------------------------------------------

                # #  Draw and save topology changes for debugging 
                # if event.type == EventType.TOPO_CHANGE:
                #     fig = plt.figure()
                #     pos = {node: event.current_topo.nodes[node]['pos'] for node in event.current_topo.nodes}
                #     nx.draw(event.current_topo,pos=pos)
                #     plt.set_loglevel("error")
                #     fig.savefig(f"{self.config.save_path}+{event.id}.png")

                # pbar.update(1)
                # pbar.set_postfix({
                #     'event_id': f'{event.id}',
                #     'event_type': f'{event.type}',
                # })

                # end show ----------------------------------------------------------------------------------------------------------------
                self.nfv_mano.handle(event)

                self.__update_from_nfv_mano(self.nfv_mano)
                
            # end this experiment
            # pbar.close()

    def __update_from_nfv_mano(self,nfv_mano:NfvMano):
        self.schedule.substrate_network = copy.deepcopy(nfv_mano.substrate_network)

            






