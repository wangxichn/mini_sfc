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
import math

class NfvScaveSummaryDefine():
    def __init__(self) -> None:
        self.SUMMARY_DATA1 = None

class NfvScaveSolverDefine():
    def __init__(self) -> None:
        self.EVENT_ID = None
        self.EVENT_TIME = None
        self.EVENT_TYPE = None

        self.SFC_LENGTH = None
        self.SFC_QOS_LATENCY = None
        self.SFC_SOLVE_TIME = None
        self.SFC_PERFORM_REVENUE = None
        self.SFC_PERFORM_NODE_RESOURCE = None
        self.SFC_PERFORM_NODE_RESOURCE_PER = None
        self.SFC_PERFORM_LINK_RESOURCE = None
        self.SFC_PERFORM_LINK_RESOURCE_PER = None

        self.MANO_VNFFG_NUM = None
        self.MANO_VNFFG_LIST = None
        self.MANO_VNFFG_RELATED = None
    

class NfvScave:
    def __init__(self,**kwargs) -> None:
        self.save_file_summary = kwargs.get("save_file_summary")
        self.save_file_solver = kwargs.get("save_file_solver")

        self.record_summary: list[NfvScaveSummaryDefine] = []
        self.record_solver: list[NfvScaveSolverDefine] = []

    def save_summary_record(self):
        pass

    def save_solver_record(self,save_data:NfvScaveSolverDefine):
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
