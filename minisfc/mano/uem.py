#Anaconda/envs/minisfc python
# -*- coding: utf-8 -*-
'''
uem.py
=========

.. module:: uem
  :platform: Linux
  :synopsis: Module for ue management functionality.

.. moduleauthor:: WangXi

Introduction
-----------

This module implements ue management functionality, primarily used in SFC applications. It provides the following features:

- Supports UE management operations (e.g., registration, deregistration, etc.).

Version
-------

- Version 1.0 (2025/03/13): Initial version

'''

from string import Template
import re
import copy
import docker
import numpy as np
import requests
import threading
import time
from datetime import datetime

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from minisfc.mano.vim import NfvVim
    from minisfc.mano.vnfm import VnfEm
    from mininet.node import Docker


class UeManager:
    def __init__(self):
        self.uePoolDict:dict[int:Ue] = {}
        self.ueServicePoolDict:dict[tuple:dict[str:float]] = {}
    
    def ready(self, nfvVim:'NfvVim'):
        self.nfvVim = nfvVim

    def add_ue_into_pool(self,ue_template:'Ue'):
        ue_id = ue_template.ue_id
        if ue_id in self.uePoolDict:
            raise ValueError(f'UE ID {ue_id} already exists in UE pool')
        else:
            self.uePoolDict[ue_id] = ue_template
    
    def add_ue_service_into_pool(self,ue_id_1:int,ue_id_2:int,**kwargs):
        if ue_id_1 not in self.uePoolDict or ue_id_2 not in self.uePoolDict:
            raise ValueError(f'UE ID {ue_id_1} or {ue_id_2} does not exist in UE pool')
        elif (ue_id_1,ue_id_2) in self.ueServicePoolDict:
            raise ValueError(f'Service between UE {ue_id_1} and UE {ue_id_2} already exists in UE service pool')
        else:
            self.ueServicePoolDict[(ue_id_1,ue_id_2)] = kwargs

    def get_ue_from_pool(self,ue_id:int) -> 'Ue':
        if ue_id not in self.uePoolDict:
            raise ValueError(f'UE ID {ue_id} does not exist in UE pool')
        ue = copy.deepcopy(self.uePoolDict[ue_id])
        return ue


class Ue:
    def __init__(self, **kwargs):
        self.ue_name = kwargs.get('ue_name', f's*u*')
        self.ue_id = kwargs.get('ue_id', None)
        self.ue_type = kwargs.get('ue_type', None)
        self.ue_ip = kwargs.get('ue_ip', None)
        self.ue_ip_control = kwargs.get('ue_ip_control', None)
        self.ue_port = kwargs.get('ue_port', None)
        self.ue_img = kwargs.get('ue_img', None)
        self.ue_aim: VnfEm = kwargs.get('ue_aim', None)
        self.ue_container_handle: Docker = kwargs.get('ue_container_handle', None)

        for key,value in kwargs.items():
            setattr(self,key,value)        
    

    def update_ue_info(self, **kwargs):
        for key,value in kwargs.items():
            setattr(self,key,value)        


    def ready(self):
        self.check_image_exists()
        self.check_cmd_param_exists()


    def config_network(self):
        if None in [self.ue_ip,self.ue_ip_control]:
            raise ValueError(f'Missing IP address for UE {self.ue_id}')
        
        self.ue_container_handle.cmd(f"ifconfig eth0 {self.ue_ip_control} netmask 255.0.0.0 up")
        self.ue_container_handle.cmd(f"ifconfig {self.ue_name}-eth0 {self.ue_ip} netmask 255.0.0.0 up")


    def check_image_exists(self):
        # Initialize a Docker client using the environment configuration
        client = docker.from_env()
        try:
            # Attempt to retrieve the image by name
            image = client.images.get(self.ue_img)
        except docker.errors.ImageNotFound:
            raise ValueError(f'Image {self.ue_img} does not exist for UE {self.ue_id}')
        except docker.errors.APIError as e:
            raise ValueError(f'Error retrieving image {self.ue_img} for UE {self.ue_id}: {e}')
            

    def check_cmd_param_exists(self):
        cmd_required_param_list = re.findall(r'\$\w+', self.ue_cmd)
        cmd_required_param_list = [param[1:] for param in cmd_required_param_list]
        cmd_template = Template(self.ue_cmd)
        missing_param_list = [param for param in cmd_required_param_list if param not in vars(self) or vars(self)[param] == None]
        if missing_param_list:
            raise ValueError(f'Missing required parameters {missing_param_list} for UE {self.ue_id} command')
        else:
            try:
                self.ue_cmd = cmd_template.substitute(**vars(self))
            except KeyError as e:
                raise ValueError(f'Missing required parameter {e} for UE {self.ue_id} command')


    def get_self_service_url(self):
        self.service_url = f"http://{self.ue_ip}:{self.ue_port}/{self.ue_type}"
        return self.service_url
    

    def get_self_control_url(self):
        self.control_url = f"http://{self.ue_ip_control}:{self.ue_port}/{self.ue_type}"
        return self.control_url


    def start_trasport(self):
        if self.ue_type == 'ue_post':
            if self.ue_aim == None:
                raise ValueError(f'UE {self.ue_name} has no aim VNF')
            self.trasport_stop_event = threading.Event()
            transport_thread = threading.Thread(target=self.__continuous_post, args=(self.ue_aim,))
            transport_thread.start()


    def stop_trasport(self):
        if self.ue_type == 'ue_post':
            try:
                self.trasport_stop_event.set()
            except AttributeError:
                raise ValueError(f'UE {self.ue_name} has not started transport')
        

    def __continuous_post(self, next_vnf_em: 'VnfEm'):
        while not self.trasport_stop_event.is_set():
            def generate_invertible_matrix(size=10):
                while True:
                    matrix = np.random.rand(size, size)
                    det = np.linalg.det(matrix)
                    if abs(det) > 1e-10:
                        return matrix
            matrix_data = generate_invertible_matrix(50)
            timestamp = datetime.now().strftime('%H%M%S%f')[:-3]
            data = {'ue_post_url': next_vnf_em.get_self_service_url(),
                    'ue_post_data': matrix_data.tolist(),
                    'request_id': int(timestamp)}
            
            try:
                response = requests.post(self.get_self_control_url(), json=data, timeout=5)
                
                if response.status_code == 200:
                    print(f'INFO: UE {self.ue_name} post request matrix inv successfully')
                else:
                    error_message = response.json().get('message', 'Unknown error')
                    print(f'WARNING: UE {self.ue_name} failed matrix inv: {response.status_code} | {error_message}')
            except Exception as e:
                print(f'ERROR: Request failed with exception {e}')

            time_interval = 1
            if self.trasport_stop_event.wait(time_interval):
                break
