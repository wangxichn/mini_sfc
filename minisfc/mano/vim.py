#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   nfv_vim.py
@Time    :   2024/01/14 21:37:19
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from mininet.net import Containernet
from mininet.node import Switch
from mininet.link import TCLink
from minisfc.topo import SubstrateTopo
from minisfc.mano.vnfm import VnfEm

import copy
    
class NfvVim:
    def __init__(self, name='NFV-VIM'):
        self.name = name
        self.nfv_instance_group: dict[int:NfvInstance] = {}


    def ready(self,substrateTopo:SubstrateTopo,containernet_handle:Containernet=None):
        self.last_substrate_topo = None
        self.substrateTopo = copy.deepcopy(substrateTopo)
        self.containernet_handle = containernet_handle

        if self.containernet_handle != None:
            # ready for containernet
            self.node_switch_map: dict[int, Switch] = {}
            for node_temp in list(self.substrateTopo.nodes):
                temple_switch = self.containernet_handle.addSwitch(f's_{node_temp}')
                self.node_switch_map[node_temp] = temple_switch

            for edge_temp in self.substrateTopo.edges:
                if edge_temp[0] == edge_temp[1]:
                    continue
                self.containernet_handle.addLink(self.node_switch_map[edge_temp[0]], self.node_switch_map[edge_temp[1]], cls=TCLink, 
                                            delay=f"{self.substrateTopo.edges[edge_temp]['weight']}ms", 
                                            bw=self.substrateTopo.edges[edge_temp]['capacity_band'])
        

        self.nfv_instance_group = {}
        for node in list(self.substrateTopo.nodes):
            self.add_NFVInstance(node_id=node,name=f"NVFI-{node}",cpu=1,ram=1,rom=1,
                                  switch=self.node_switch_map[node] if containernet_handle != None else None)


    def add_NFVInstance(self,node_id,name,cpu:float,ram:float,rom:float,
                         switch:Switch = None,image=None,ip=None,port=None):
        nfv_instance = NfvInstance(node_id,name,cpu,ram,rom,switch,image,ip,port)
        self.nfv_instance_group[node_id] = nfv_instance
    

    def del_NFVInstance(self,node_id):
        if node_id in self.nfv_instance_group:
            del self.nfv_instance_group[node_id]
    

    def deploy_VNF(self,vnf_em:VnfEm,NFVI_node_id):
        nfv_instance: NfvInstance = self.nfv_instance_group.get(NFVI_node_id, None)
        if nfv_instance != None:
            nfv_instance.deploy_VNF(vnf_em,containernet_handle=self.containernet_handle)

            self.substrateTopo.opt_node_attrs_value(NFVI_node_id,'remain_cpu','decrease',vnf_em.cpu_req)
            self.substrateTopo.opt_node_attrs_value(NFVI_node_id,'remain_ram','decrease',vnf_em.ram_req)
            # self.substrateTopo.opt_node_attrs_value(NFVI_node_id,'remain_rom','decrease',vnf_em.rom_req)

            return True
        return False
    

    def undeploy_VNF(self,vnf_em_name:str,NFVI_node_id):
        nfv_instance: NfvInstance = self.nfv_instance_group.get(NFVI_node_id, None)
        if nfv_instance != None:
            if vnf_em_name in nfv_instance.get_deployed_vnfs():
                vnf_em = [vnf_em for vnf_em in nfv_instance.deployed_vnf if vnf_em.name == vnf_em_name]
                nfv_instance.undeploy_VNF(vnf_em[0],containernet_handle=self.containernet_handle)

                self.substrateTopo.opt_node_attrs_value(NFVI_node_id,'remain_cpu','increase',vnf_em[0].cpu_req)
                self.substrateTopo.opt_node_attrs_value(NFVI_node_id,'remain_ram','increase',vnf_em[0].ram_req)
                # self.substrateTopo.opt_node_attrs_value(NFVI_node_id,'remain_rom','increase',vnf_em[0].rom_req)

                return True
        return False
    
    def deploy_service(self,NFVI_node_id_1,NFVI_node_id_2,service_bw):
        self.substrateTopo.opt_link_attrs_value((NFVI_node_id_1,NFVI_node_id_2),'remain_band','decrease',service_bw)
    
    def undeploy_service(self,NFVI_node_id_1,NFVI_node_id_2,service_bw):
        self.substrateTopo.opt_link_attrs_value((NFVI_node_id_1,NFVI_node_id_2),'remain_band','increase',service_bw)

    def update_substrate_topo(self,substrateTopo:SubstrateTopo):
        self.last_substrate_topo = self.substrateTopo
        self.substrateTopo = copy.deepcopy(substrateTopo)
        

    def get_curent_substrate_topo(self):
        return copy.deepcopy(self.substrateTopo)
    

class NfvInstance:
    def __init__(self,node_id,name,cpu:float,ram:float,rom:float,
                 switch:'Switch' = None,image=None,ip=None,port=None):
        self.node_id = node_id
        self.name = name
        self.cpu_capacity = cpu
        self.cpu_remain = cpu
        self.ram_capacity = ram
        self.ram_remain = ram
        self.rom_capacity = rom
        self.rom_remain = rom

        self.switch = switch
        self.image = image
        self.ip = ip
        self.port = port

        self.deployed_vnf: list[VnfEm] = []
    
    def deploy_VNF(self,vnf_em:VnfEm,containernet_handle:Containernet=None):
        # if containernet_handle != None:

        #     containernet_handle.addDocker(name=vnf_em.name, ip=f"{self.ip}:{self.port}", dimage=vnf_em.image,
        #                                     volumes=[f"{self.switch.name}:/mnt/switch"],
        #                                     command=f"python3 /mnt/switch/vnf_em.py {vnf_em.name} {self.switch.name}")



        self.deployed_vnf.append(vnf_em)
        self.cpu_remain -= vnf_em.cpu_req
        self.ram_remain -= vnf_em.ram_req
        self.rom_remain -= vnf_em.rom_req
    
    def undeploy_VNF(self,vnf_em:VnfEm,containernet_handle:Containernet=None):
        self.deployed_vnf.remove(vnf_em)
        self.cpu_remain += vnf_em.cpu_req
        self.ram_remain += vnf_em.ram_req
        self.rom_remain += vnf_em.rom_req
        
    def get_deployed_vnfs(self):
        return [vnf_em.name for vnf_em in self.deployed_vnf]
        

    