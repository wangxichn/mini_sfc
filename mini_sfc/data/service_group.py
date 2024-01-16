#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   service_group.py
@Time    :   2024/01/12 20:58:40
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from data import Config
from data import ServiceChain
from utils import NumberOperator
import numpy as np
import code

class ServiceGroup(list[ServiceChain]):
    def __init__(self, config:Config) -> None:
        super().__init__()
        
        self.config = config
        self.num_sfc = config.service_group_setting["num_sfc"]
        self.arrival_rate_setting = config.service_group_setting["arrival_rate_setting"]
        self.lifetime_setting = config.service_group_setting["lifetime_setting"]
        self.qos_latency_setting = config.service_group_setting["qos_latency_setting"]

        self.__generate_service_chains()


    def __generate_service_chains(self):
        arrivetime_interval = NumberOperator.generate_data_with_distribution(size=self.num_sfc, **self.arrival_rate_setting)
        arrivetime_value = np.cumsum(arrivetime_interval)
        lifetime_value = NumberOperator.generate_data_with_distribution(self.num_sfc,**self.lifetime_setting)
        qos_latency_value = NumberOperator.generate_data_with_distribution(self.num_sfc,**self.qos_latency_setting)

        for i in range(self.num_sfc):
            service_chain = ServiceChain(self.config,**{"id":i,"arrivetime":arrivetime_value[i],"lifetime":lifetime_value[i],"qos_latency":qos_latency_value[i]})
            self.append(service_chain)
            
    def append(self, __object: ServiceChain) -> None:
        return super().append(__object)
