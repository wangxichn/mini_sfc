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

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from minisfc.mano.vim import NfvVim
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
        self.ue_aim: Ue = kwargs.get('ue_aim', None)
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


