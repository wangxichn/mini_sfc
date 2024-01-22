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
import shutil
import yaml
import time
import socket
import logging
import code


class Config:
    def __init__(self,**kwargs):
        setting_file_name = kwargs.get("setting_file_name","setting.yaml")
        self.setting_path: str = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")),f"settings\{setting_file_name}")
        self.save_path: str = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")),f"save\{self.get_run_id()}/")

        self.read_settings(self.setting_path)
        self.ready_for_directory(self.save_path)
        shutil.copy(self.setting_path,self.save_path)

    def read_settings(self,filepath):
        logging.info(f"Try to read seting from file: {filepath}")

        content = self.__read_settings_from_yaml(filepath)
        self.scenario_setting:dict = content["scenario_setting"]
        self.mano_setting:dict = content["mano_setting"]
        self.substrate_network_setting:dict = content["substrate_network_setting"]
        self.service_group_setting:dict = content["service_group_setting"]
        self.service_chain_setting:dict = content["service_chain_setting"]

        # code.interact(banner="",local=locals())

    @staticmethod
    def get_run_id() -> str:
        run_time = time.strftime('%Y%m%dT%H%M%S')
        host_name = socket.gethostname()
        run_id = f'{host_name}-{run_time}'
        return run_id
        
    def __read_settings_from_yaml(self,filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            if filepath[-4:] == 'yaml':
                setting_dict = yaml.load(f, Loader=yaml.Loader)
            else:
                return ValueError('Only supports settings files in yaml format!')
        return setting_dict

    @staticmethod
    def ready_for_directory(path:str) -> str:
        if not os.path.exists(path):
            os.makedirs(path)
        return path





