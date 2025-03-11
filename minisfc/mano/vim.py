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
    
class NfvVim:
    def __init__(self, name='NFV-VIM'):
        self.name = name
        self.nfv_instance_group: list[NfvInstance] = []

    def ready(self,substrateTopo:'SubstrateTopo',container_net:'Containernet'=None):
        self.substrateTopo = substrateTopo
        self.container_net = container_net

        if container_net != None:
            # ready for containernet
            self.node_switch_map: dict[int, Switch] = {}
            for node_temp in list(self.substrateTopo.nodes):
                temple_switch = self.container_net.addSwitch(f's_{node_temp}')
                self.node_switch_map[node_temp] = temple_switch

            for edge_temp in self.substrateTopo.edges:
                if edge_temp[0] == edge_temp[1]:
                    continue
                self.container_net.addLink(self.node_switch_map[edge_temp[0]], self.node_switch_map[edge_temp[1]], cls=TCLink, 
                                            delay=f"{self.substrateTopo.edges[edge_temp]['weight']}ms", 
                                            bw=self.substrateTopo.edges[edge_temp]['capacity_band'])
        

        self.nfv_instance_group.clear()
        for node in list(self.substrateTopo.nodes):
            self.add_nfv_instance(node_id=node,name=f"NVFI-{node}",cpu=1,ram=1,rom=1,
                                  switch=self.node_switch_map[node] if container_net != None else None)
            
    def add_nfv_instance(self,node_id,name,cpu:float,ram:float,rom:float,
                         switch:'Switch' = None,image=None,ip=None,port=None):
        nfv_instance = NfvInstance(node_id,name,cpu,ram,rom,switch,image,ip,port)
        self.nfv_instance_group.append(nfv_instance)
    
    def del_nfv_instance(self,name):
        for nfv_instance in self.nfv_instance_group:
            if nfv_instance.name == name:
                self.nfv_instance_group.remove(nfv_instance)
                return True
        return False

class NfvInstance:
    def __init__(self,node_id,name,cpu:float,ram:float,rom:float,
                 switch:'Switch' = None,image=None,ip=None,port=None):
        self.node_id = node_id
        self.name = name
        self.cpu = cpu
        self.ram = ram
        self.rom = rom
        self.switch = switch
        self.image = image
        self.ip = ip
        self.port = port
    