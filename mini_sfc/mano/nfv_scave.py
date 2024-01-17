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

from base import Event, EventType
from mano import NfvOrchestrator
from solvers import SolutionGroup, SOLUTION_TYPE

class NfvScaveSummaryData():
    def __init__(self) -> None:
        self.SUMMARY_DATA1 = None

class NfvScaveSolverData():
    def __init__(self) -> None:
        self.EVENT_ID = None
        self.EVENT_TIME = None
        self.EVENT_TYPE = None

        self.SFC_LENGTH = None
        self.SFC_QOS_LATENCY = None
        self.SFC_SOLVE_TIME = None
        self.SFC_REVENUE = None

        self.MANO_VNFFG_NUM = None
        self.MANO_VNFFG_LIST = None
        self.MANO_VNFFG_RELATED = None
        self.MANO_RESOURSE_NODE_PER = [0,0,0,0]
        self.MANO_RESOURSE_LINK_PER = [0]
    

class NfvScave:
    def __init__(self,**kwargs) -> None:
        self.save_file_summary = kwargs.get("save_file_summary")
        self.save_file_solver = kwargs.get("save_file_solver")

        self.record_summary: list[NfvScaveSummaryData] = []
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
        
        for vnffg in nfv_orchestrator.vnffg_group:
            data_save.MANO_RESOURSE_NODE_PER = np.sum([data_save.MANO_RESOURSE_NODE_PER, vnffg.solution_group[-1].cost_node_resource_percentage], axis=0).tolist()
            data_save.MANO_RESOURSE_LINK_PER = np.sum([data_save.MANO_RESOURSE_LINK_PER, vnffg.solution_group[-1].cost_link_resource_percentage], axis=0).tolist()
        data_save.MANO_RESOURSE_NODE_PER = ['%.5f'% data for data in data_save.MANO_RESOURSE_NODE_PER]
        data_save.MANO_RESOURSE_LINK_PER = ['%.5f'% data for data in data_save.MANO_RESOURSE_LINK_PER]


        if event.type == EventType.SFC_ARRIVE:
            data_save.SFC_LENGTH = event.sfc.num_nodes
            data_save.SFC_QOS_LATENCY = '%.3f'% event.sfc.qos_latency
            data_save.SFC_SOLVE_TIME = '%.3f'% nfv_orchestrator.vnffg_group_log.get(event.sfc.id)[-1].cost_real_time
        
        if event.type == EventType.SFC_ENDING:
            data_save.SFC_REVENUE = '%.3f'% nfv_orchestrator.vnffg_group_log.get(event.sfc.id)[-1].perform_revenue

        if event.type in (EventType.SFC_ARRIVE, EventType.SFC_ENDING):
            data_save.MANO_VNFFG_RELATED = [event.sfc.id]
            # data_save.SFC_PERFORM_NODE_RESOURCE = nfv_orchestrator.vnffg_group_log.get(event.sfc.id)[-1].cost_node_resource
            # data_save.SFC_PERFORM_NODE_RESOURCE_PER = nfv_orchestrator.vnffg_group_log.get(event.sfc.id)[-1].cost_node_resource_percentage
            # data_save.SFC_PERFORM_LINK_RESOURCE = nfv_orchestrator.vnffg_group_log.get(event.sfc.id)[-1].cost_link_resource
            # data_save.SFC_PERFORM_LINK_RESOURCE_PER = nfv_orchestrator.vnffg_group_log.get(event.sfc.id)[-1].cost_link_resource_percentage

        if event.type == EventType.TOPO_CHANGE:
            data_save.MANO_VNFFG_RELATED = [id for id in nfv_orchestrator.vnffg_group_log.keys() 
                                            if nfv_orchestrator.vnffg_group_log.get(id)[-1].current_description == SOLUTION_TYPE.CHANGE_SUCCESS]

        self.save_solver_record(data_save)
        self.record_solver.append(data_save)


    def handle_summary_data(self, vnffg_group_log:dict[int,SolutionGroup]):

        pass

    def save_summary_record(self):
        pass

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
