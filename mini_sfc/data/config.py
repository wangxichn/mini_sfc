#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   config.py
@Time    :   2024/01/11 19:03:08
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from dataclasses import dataclass
import os
import yaml
import time
import socket
import logging
import code


@dataclass
class Config:
    setting_path: str = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")),"settings\setting.yaml")
    save_path: str = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")),"save/")

    def __post_init__(self):
        self.read_settings(self.setting_path)
        self.get_run_id()
        self.ready_for_directory(self.save_path)

    def read_settings(self,filepath):
        logging.info(f"Try to read seting from file: {filepath}")

        content = self.__read_settings_from_yaml(filepath)
        self.scenario_setting:dict = content["scenario_setting"]
        self.substrate_network_setting:dict = content["substrate_network_setting"]
        self.service_group_setting:dict = content["service_group_setting"]
        self.service_chain_setting:dict = content["service_chain_setting"]

        # code.interact(banner="",local=locals())

    def get_run_id(self):
        self.run_time = time.strftime('%Y%m%dT%H%M%S')
        self.host_name = socket.gethostname()
        self.run_id = f'{self.host_name}-{self.run_time}'
        
    def __read_settings_from_yaml(self,filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            if filepath[-4:] == 'yaml':
                setting_dict = yaml.load(f, Loader=yaml.Loader)
            else:
                return ValueError('Only supports settings files in yaml format!')
        return setting_dict

    @staticmethod
    def ready_for_directory(path:str):
        if not os.path.exists(path):
            os.mkdir(path)





