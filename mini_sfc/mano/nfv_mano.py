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
from data import ServiceChain
from mano import NfvOrchestrator
from base import EventType, Event
from mano import NfvVim
from mano import NfvScave, NfvScaveSolverDefine, NfvScaveSummaryDefine
from solvers import SolutionGroup
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

        data_save = NfvScaveSolverDefine()
        data_save.PHYNODE_ALL_CPU_BEFORE = sum(self.substrate_network.get_all_nodes_attrs_values("cpu_setting","remain_setting"))
        data_save.PHYNODE_ALL_ENG_BEFORE = sum(self.substrate_network.get_all_nodes_attrs_values("energy_setting","remain_setting"))

        self.substrate_network, solutions_log = self.nfv_orchestrator.handle(event)

        
        data_save.EVENT_ID = event.id
        data_save.EVENT_TYPE = event.type
        data_save.EVENT_TIME = event.time
        data_save.MANO_VNFFG_NUM = len(self.nfv_orchestrator.vnffg_group)
        data_save.MANO_VNFFG_LIST = [i.service_chain.id for i in self.nfv_orchestrator.vnffg_group]
        data_save.PHYNODE_ALL_CPU_AFTER = sum(self.substrate_network.get_all_nodes_attrs_values("cpu_setting","remain_setting"))
        data_save.PHYNODE_ALL_ENG_AFTER = sum(self.substrate_network.get_all_nodes_attrs_values("energy_setting","remain_setting"))

        if event.type == EventType.SFC_ARRIVE:
            data_save.SFC_LENGTH = event.sfc.num_nodes
            data_save.SFC_QOS_LATENCY = event.sfc.qos_latency
            data_save.SFC_SET_SOLVE_TIME = solutions_log.get(event.sfc.id)[-1].cost_real_time
        
        if event.type == EventType.SFC_ENDING:
            data_save.SFC_REVENUE = solutions_log.get(event.sfc.id)[-1].perform_revenue

        self.nfv_scave.save_solver_record(data_save)
        self.nfv_scave.record_solver.append(data_save)


