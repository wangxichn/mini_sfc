#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   nfv_scave.py
@Time    :   2024/01/14 21:37:40
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

import code
import csv
import os
import numpy as np
import copy

from base import Event, EventType
from mano import NfvOrchestrator
from solvers import SolutionGroup, SOLUTION_TYPE, SOLVER_REGISTRAR

class NfvScaveSummaryData:
    """ Scave while an experiment ending
    """
    def __init__(self) -> None:
        self.EXP_ID = None
        self.SUBSTRATE_NODE = None
        self.SERVICE_NUM = None
        self.SOLVER_NAME = None
        self.SOLVER_AVER_TIME = None
        self.COMPLETION_RATE = None
        self.SUM_REVENUE = None
        self.LANGTERM_REVENUE = None
        

class NfvScaveSolverData:
    """ Scave while an event ending
    """
    def __init__(self) -> None:
        self.EVENT_ID = None
        self.EVENT_TIME = None
        self.EVENT_TYPE = None

        self.SFC_LENGTH = None
        self.SFC_LIFETIME = None
        self.SFC_QOS_LATENCY = None
        self.SFC_LATENCY_ALL = None
        self.SFC_LATENCY_RUN = None
        self.SFC_LATENCY_MAP = None
        self.SFC_LATENCY_ROUTE = None
        self.SFC_SOLVE_TIME = None
        self.SFC_REVENUE = None
        self.SFC_DESCRIPRION = None

        self.MANO_VNFFG_NUM = None
        self.MANO_VNFFG_LIST = None
        self.MANO_VNFFG_RELATED = None
        self.MANO_RESOURSE_NODE_PER = [0,0,0,0]
        self.MANO_RESOURSE_LINK_PER = [0]
        self.MANO_RESOURSE_NODE_CPU = None
        self.MANO_RESOURSE_NODE_RAM = None
        self.MANO_RESOURSE_NODE_DISK = None
        self.MANO_RESOURSE_NODE_ENG = None

class NfvScave:
    count = 0
    def __init__(self,**kwargs) -> None:
        NfvScave.count += 1

        self.save_file_summary = kwargs.get("save_file_summary")
        self.save_file_solver = kwargs.get("save_file_solver")

        self.record_solver: list[NfvScaveSolverData] = []
    
    def handle_solver_data(self, event:Event, nfv_orchestrator:NfvOrchestrator):
        """ Record solver performance after each event 

        Args:
            event (Event): A event MAMO receives from scenes 
            nfv_orchestrator (NfvOrchestrator): Status of current NFV orchestrator 
        """
        data_save = NfvScaveSolverData()

        data_save.EVENT_ID = event.id
        data_save.EVENT_TYPE = event.type
        data_save.EVENT_TIME = '%.3f'% event.time

        data_save.MANO_VNFFG_NUM = len(nfv_orchestrator.vnffg_group)
        data_save.MANO_VNFFG_LIST = [i.service_chain.id for i in nfv_orchestrator.vnffg_group]
        
        # Percentage of resources used to obtain all presence services
        for vnffg in nfv_orchestrator.vnffg_group:
            data_save.MANO_RESOURSE_NODE_PER = np.sum([data_save.MANO_RESOURSE_NODE_PER, vnffg.solution_group[-1].cost_node_resource_percentage], axis=0).tolist()
            data_save.MANO_RESOURSE_LINK_PER = np.sum([data_save.MANO_RESOURSE_LINK_PER, vnffg.solution_group[-1].cost_link_resource_percentage], axis=0).tolist()
        # Calculate the proportion of remaining network resources
        data_save.MANO_RESOURSE_NODE_PER = ['%.5f'% (1-data) for data in data_save.MANO_RESOURSE_NODE_PER]
        data_save.MANO_RESOURSE_LINK_PER = ['%.5f'% (1-data) for data in data_save.MANO_RESOURSE_LINK_PER]

        # Calculate total remaining resources
        data_save.MANO_RESOURSE_NODE_CPU = sum(event.current_substrate.get_all_nodes_attrs_values("cpu_setting","remain_setting"))
        data_save.MANO_RESOURSE_NODE_RAM = sum(event.current_substrate.get_all_nodes_attrs_values("ram_setting","remain_setting"))
        data_save.MANO_RESOURSE_NODE_DISK = sum(event.current_substrate.get_all_nodes_attrs_values("disk_setting","remain_setting"))
        data_save.MANO_RESOURSE_NODE_ENG = sum(event.current_substrate.get_all_nodes_attrs_values("energy_setting","remain_setting"))

        # The proportion of energy consumed needs to be calculated separately 
        data_save.MANO_RESOURSE_NODE_PER[-1] = '%.5f'% (data_save.MANO_RESOURSE_NODE_ENG/
                                                        sum(event.current_substrate.get_all_nodes_attrs_values("energy_setting","max_setting")))

        if event.type == EventType.SFC_ARRIVE:
            data_save.SFC_LENGTH = event.sfc.num_nodes
            data_save.SFC_SOLVE_TIME = '%.3f'% nfv_orchestrator.vnffg_group_log.get(event.sfc.id)[-1].cost_real_time
        
        if event.type == EventType.SFC_ENDING:
            if nfv_orchestrator.vnffg_group_log[event.sfc.id][-1].current_description == SOLUTION_TYPE.END_SUCCESS:
                # SFC normal end can calculate returns 
                solver = SOLVER_REGISTRAR.get(nfv_orchestrator.solver_name)()
                revenue = solver.get_revenue(nfv_orchestrator.vnffg_group_log[event.sfc.id])
                data_save.SFC_REVENUE = '%.3f'% revenue
                nfv_orchestrator.vnffg_group_log[event.sfc.id][-1].perform_revenue = revenue
            
        if event.type in (EventType.SFC_ARRIVE, EventType.SFC_ENDING):
            data_save.MANO_VNFFG_RELATED = [event.sfc.id]
            data_save.SFC_QOS_LATENCY = '%.3f'% event.sfc.qos_latency
            data_save.SFC_LIFETIME = event.sfc.lifetime
            data_save.SFC_LATENCY_RUN = nfv_orchestrator.vnffg_group_log.get(event.sfc.id)[-1].perform_latency_run
            data_save.SFC_LATENCY_MAP = nfv_orchestrator.vnffg_group_log.get(event.sfc.id)[-1].perform_latency_map
            data_save.SFC_LATENCY_ROUTE = nfv_orchestrator.vnffg_group_log.get(event.sfc.id)[-1].perform_latency_route
            data_save.SFC_LATENCY_ALL = nfv_orchestrator.vnffg_group_log.get(event.sfc.id)[-1].perform_latency
            data_save.SFC_DESCRIPRION = nfv_orchestrator.vnffg_group_log.get(event.sfc.id)[-1].current_description

        if event.type == EventType.TOPO_CHANGE:
            data_save.MANO_VNFFG_RELATED = [id for id in nfv_orchestrator.vnffg_group_log.keys() 
                                            if nfv_orchestrator.vnffg_group_log.get(id)[-1].current_time == event.time and
                                            nfv_orchestrator.vnffg_group_log.get(id)[-1].current_description in 
                                            (SOLUTION_TYPE.CHANGE_SUCCESS, SOLUTION_TYPE.CHANGE_NODE_FAILED_FOR_CPU,
                                             SOLUTION_TYPE.CHANGE_NODE_FAILED_FOR_RAM, SOLUTION_TYPE.CHANGE_NODE_FAILED_FOR_ENG,
                                             SOLUTION_TYPE.CHANGE_NODE_FAILED_FOR_DISK, SOLUTION_TYPE.CHANGE_LATENCY_FAILED, 
                                             SOLUTION_TYPE.CHANGE_LINK_FAILED)]

        self.save_solver_record(data_save)
        self.record_solver.append(copy.deepcopy(data_save))


    def handle_summary_data(self, nfv_orchestrator:NfvOrchestrator):
        data_save = NfvScaveSummaryData()

        data_save.EXP_ID = NfvScave.count
        data_save.SUBSTRATE_NODE = nfv_orchestrator.substrate_network.num_nodes
        data_save.SERVICE_NUM = len(nfv_orchestrator.vnffg_group_log)
        data_save.SOLVER_NAME = nfv_orchestrator.solver_name

        sfc_complete_num = 0
        sfc_revenue = []
        sfc_longterm_revenue = []
        for id in nfv_orchestrator.vnffg_group_log.keys():
            if nfv_orchestrator.vnffg_group_log[id][-1].current_description == SOLUTION_TYPE.END_SUCCESS:
                sfc_complete_num += 1
                sfc_revenue.append(nfv_orchestrator.vnffg_group_log[id][-1].perform_revenue)
                sfc_longterm_revenue.append(sfc_revenue[-1]/nfv_orchestrator.vnffg_group_log[id][-1].current_time)
        data_save.COMPLETION_RATE = '%.2f'% (sfc_complete_num/data_save.SERVICE_NUM)
        data_save.SUM_REVENUE = sum(sfc_revenue)
        data_save.LANGTERM_REVENUE = sum(sfc_longterm_revenue)

        self.save_summary_record(data_save)
        

    def save_summary_record(self,save_data:NfvScaveSummaryData):
        head = None if os.path.exists(self.save_file_summary) else list(save_data.__dict__.keys())
        with open(self.save_file_summary, 'a+', newline='') as csv_file:
            writer = csv.writer(csv_file, dialect='excel', delimiter=',')
            if head is not None: writer.writerow(head)
            writer.writerow(list(save_data.__dict__.values()))

    def save_solver_record(self,save_data:NfvScaveSolverData):
        head = None if os.path.exists(self.save_file_solver) else list(save_data.__dict__.keys())
        with open(self.save_file_solver, 'a+', newline='') as csv_file:
            writer = csv.writer(csv_file, dialect='excel', delimiter=',')
            if head is not None: writer.writerow(head)
            writer.writerow(list(save_data.__dict__.values()))

    def update_save_file_setting(self,**kwargs):
        if "save_file_summary" in kwargs:
            self.save_file_summary = kwargs.get("save_file_summary")
        if "save_file_solver" in kwargs:
            self.save_file_solver = kwargs.get("save_file_solver")
