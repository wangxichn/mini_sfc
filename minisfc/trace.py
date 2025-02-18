#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   trace.py
@Time    :   2024/06/18 22:33:22
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

import time
import socket
import csv

class Trace:
    def __init__(self):
        self.filename = None

    def set(self,filename:str = None):
        self.filename = filename

    def ready(self):
        if self.filename == None:
            self.filename = f"TRACE_{Trace.get_run_id()}.csv"
        
        self.fields = ['Event', 'Time', 'SfcId', 'Result', 'Resource', 'Vnffgs', 'Reason']
        with open(self.filename,'+w',newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self.fields)
            writer.writeheader()

    def write(self,contextDict:dict):
        with open(self.filename,'+a',newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self.fields)
            writer.writerow(contextDict)

    @staticmethod
    def get_time_stamp():
        ct = time.time()
        local_time = time.localtime(ct)
        data_head = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
        data_secs = (ct - int(ct)) * 1000
        time_stamp = "%s.%03d" % (data_head, data_secs)
        stamp = ("".join(time_stamp.split()[0].split("-"))+"".join(time_stamp.split()[1].split(":"))).replace('.', '')
        return stamp

    @staticmethod
    def get_run_id() -> str:
        run_time = Trace.get_time_stamp()
        host_name = socket.gethostname()
        run_id = f'{host_name}-{run_time}'
        return run_id
    
TRACER = Trace()
