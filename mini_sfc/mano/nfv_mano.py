#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   nfv_mano.py
@Time    :   2024/01/11 21:53:57
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from data import Config
from data import SubstrateNetwork
from mano import NfvOrchestrator
from base import Event
from mano import NfvVim
from mano import NfvScave
import code
import logging

class NfvMano:
    def __init__(self,config:Config):
        self.config = config

        # init NfvOrchestrator
        self.solver_name: str = self.config.mano_setting.get("solver_name","baseline_random")
        self.nfv_orchestrator_setting = {"solver_name":self.solver_name}
        self.nfv_orchestrator = NfvOrchestrator(**self.nfv_orchestrator_setting)

        # init NfvScave
        self.save_file_summary = self.config.save_path + "exp_summary.csv"
        self.save_file_solver = Config.ready_for_directory(self.config.save_path + f"{self.solver_name}/")+ f"{Config.get_run_id()}.csv"
        self.nfv_scave_setting = {"save_file_summary":self.save_file_summary, "save_file_solver":self.save_file_solver}
        self.nfv_scave = NfvScave(**self.nfv_scave_setting)


    def ready(self,substrate_network:SubstrateNetwork):
        logging.info("Nfv Mano is initializing")

        # ready for nfv scave
        self.save_file_solver = Config.ready_for_directory(self.config.save_path + f"{self.solver_name}/")+ f"{Config.get_run_id()}.csv"
        self.nfv_scave_setting = {"save_file_solver":self.save_file_solver}
        self.nfv_scave.update_save_file_setting(**self.nfv_scave_setting)
        self.nfv_scave.record_solver.clear()

        # update substate network
        self.substrate_network = substrate_network

        # ready for vims
        self.nfv_vim_group:list[NfvVim] = [NfvVim(**substrate_network.nodes[i]) for i in substrate_network.nodes]

        # ready for nfv orchestrator
        self.nfv_orchestrator.ready(substrate_network)

    
    def handle(self,event:Event):
        # Send the event to MANO for processing, and update the substrate network according to the processing results 
        self.substrate_network = self.nfv_orchestrator.handle(event)
        # Use Scave to analyze and document the handling of this event 
        self.nfv_scave.handle_solver_data(event,self.nfv_orchestrator)

        


