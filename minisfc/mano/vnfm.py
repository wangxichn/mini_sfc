#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   nfv_manager.py
@Time    :   2024/06/18 15:15:00
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''


from string import Template
import re
import copy
import docker
import requests

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from minisfc.mano.vim import NfvVim
    from minisfc.mano.uem import Ue
    from mininet.node import Docker


class VnfManager:
    def __init__(self):
        """_summary_

        Args:
            vnfParamDict (dict[int:dict[str]]): {id:{paramtype:value}}
        """
        self.vnfPoolDict:dict[int:VnfEm] = {}
        self.vnfServicePoolDict:dict[tuple:dict[str:float]] = {}


    def ready(self, nfvVim:'NfvVim'):
        self.nfvVim = nfvVim


    def add_vnf_into_pool(self,vnfEm_template:'VnfEm'):
        vnf_id = vnfEm_template.vnf_id
        if vnf_id in self.vnfPoolDict:
            raise ValueError(f'VNF ID {vnf_id} already exists in VNF pool')
        else:
            self.vnfPoolDict[vnf_id] = vnfEm_template
    

    def add_vnf_service_into_pool(self,vnf_id_1:int,vnf_id_2:int,**kwargs):
        if vnf_id_1 not in self.vnfPoolDict or vnf_id_2 not in self.vnfPoolDict:
            raise ValueError(f'VNF ID {vnf_id_1} or {vnf_id_2} does not exist in VNF pool')
        elif (vnf_id_1,vnf_id_2) in self.vnfServicePoolDict:
            raise ValueError(f'Service between VNF {vnf_id_1} and VNF {vnf_id_2} already exists in VNF service pool')
        else:
            self.vnfServicePoolDict[(vnf_id_1,vnf_id_2)] = kwargs


    def get_vnf_from_pool(self,vnf_id:int) -> 'VnfEm':
        if vnf_id not in self.vnfPoolDict:
            raise ValueError(f'VNF ID {vnf_id} does not exist in VNF pool')
        vnfEm = copy.deepcopy(self.vnfPoolDict[vnf_id])
        return vnfEm
    

    def set_vnfs_forward_route(self,vnfs:list['VnfEm'],ues:list['Ue']):
        for i, vnf_em in enumerate(vnfs):
            if i != len(vnfs)-1:
                vnf_em.set_forward_route(ues[0],vnfs[i+1].get_self_service_url())
            else:
                vnf_em.set_forward_route(ues[0],ues[1].get_self_service_url())
                
        
class VnfEm:
    def __init__(self,**kwargs):
        """VNF Element Management

        Args:
            
        """
        self.vnf_name:str = kwargs.get('vnf_name',f's*f*')
        self.vnf_id:int = kwargs.get('vnf_id',None)
        self.vnf_cpu:float = kwargs.get('vnf_cpu',0)
        self.vnf_ram:float = kwargs.get('vnf_ram',0)
        self.vnf_rom:float = kwargs.get('vnf_rom',0)

        self.vnf_container_handle:'Docker' = kwargs.get('vnf_container_handle',None)
        self.vnf_type:str = kwargs.get('vnf_type',None)
        self.vnf_img:str = kwargs.get('vnf_img',None)
        self.vnf_ip:str = kwargs.get('vnf_ip',None)
        self.vnf_ip_control:str = kwargs.get('vnf_ip_control',None)
        self.vnf_port:int = kwargs.get('vnf_port',None)
        self.vnf_cmd:str = kwargs.get('vnf_cmd',None)

        for key,value in kwargs.items():
            setattr(self,key,value)


    def update_vnf_param(self,**kwargs):
        for key,value in kwargs.items():
            setattr(self,key,value)


    def ready(self):
        self.check_image_exists()
        self.check_cmd_param_exists()


    def config_network(self):
        if None in [self.vnf_ip,self.vnf_ip_control]:
            raise ValueError(f'Missing IP address for VNF {self.vnf_id}')
        
        self.vnf_container_handle.cmd(f"ifconfig eth0 {self.vnf_ip_control} netmask 255.0.0.0 up")
        self.vnf_container_handle.cmd(f"ifconfig {self.vnf_name}-eth0 {self.vnf_ip} netmask 255.0.0.0 up")


    def check_image_exists(self):
        # Initialize a Docker client using the environment configuration
        client = docker.from_env()
        try:
            # Attempt to retrieve the image by name
            image = client.images.get(self.vnf_img)
        except docker.errors.ImageNotFound:
            raise ValueError(f'Image {self.vnf_img} does not exist for VNF {self.vnf_id}')
        except docker.errors.APIError as e:
            raise ValueError(f'Error retrieving image {self.vnf_img} for VNF {self.vnf_id}: {e}')
            

    def check_cmd_param_exists(self):
        cmd_required_param_list = re.findall(r'\$\w+', self.vnf_cmd)
        cmd_required_param_list = [param[1:] for param in cmd_required_param_list]
        cmd_template = Template(self.vnf_cmd)
        missing_param_list = [param for param in cmd_required_param_list if param not in vars(self) or vars(self)[param] == None]
        if missing_param_list:
            raise ValueError(f'Missing required parameters {missing_param_list} for VNF {self.vnf_id} command')
        else:
            try:
                self.vnf_cmd = cmd_template.substitute(**vars(self))
            except KeyError as e:
                raise ValueError(f'Missing required parameter {e} for VNF {self.vnf_id} command')
            

    def set_forward_route(self,traffic_from_ue:'Ue',traffic_to_url:str):
        vnf_opt_url = f"http://{self.vnf_ip_control}:{self.vnf_port}/set_route"

        data = {'traffic_from_ue': traffic_from_ue.ue_name,
                'traffic_to_url': traffic_to_url}
        
        response = requests.post(vnf_opt_url, json=data)

        if response.status_code == 200:
            print(f'INFO: VNF {self.vnf_name} forward route set successfully')
        else:
            error_message = response.json().get('message', 'Unknown error')
            print(f'WARNING: Failed to set VNF {self.vnf_name} forward route: {response.status_code} | {error_message}')

    
    def get_self_service_url(self):
        self.service_url = f"http://{self.vnf_ip}:{self.vnf_port}/{self.vnf_type}"
        return self.service_url
    
    
    def get_self_control_url(self):
        self.control_url = f"http://{self.vnf_ip_control}:{self.vnf_port}/{self.vnf_type}"
        return self.control_url
            