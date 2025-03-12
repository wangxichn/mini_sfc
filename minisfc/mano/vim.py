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
        self.ip_prefix = '10.0.'
        self.ips_assigned: set[str] = set()
        self.ip_control_prefix = '172.17.'
        self.ips_control_assigned: set[str] = set()


    def ready(self,substrateTopo:SubstrateTopo,containernet_handle:Containernet=None):
        self.last_substrate_topo = None
        self.substrateTopo = copy.deepcopy(substrateTopo)
        self.containernet_handle = containernet_handle

        if self.containernet_handle != None:
            # ready for containernet
            self.node_switch_map: dict[int, Switch] = {}
            for node_temp in list(self.substrateTopo.nodes):
                temple_switch = self.containernet_handle.addSwitch(f's{node_temp}')
                self.node_switch_map[node_temp] = temple_switch

            for edge_temp in self.substrateTopo.edges:
                if edge_temp[0] == edge_temp[1]:
                    continue
                self.containernet_handle.addLink(self.node_switch_map[edge_temp[0]], 
                                                 self.node_switch_map[edge_temp[1]], cls=TCLink, 
                                                 delay=f"{self.substrateTopo.edges[edge_temp]['weight']}ms", 
                                                 bw=self.substrateTopo.edges[edge_temp]['capacity_band'])
        

        self.nfv_instance_group = {}
        for node in list(self.substrateTopo.nodes):
            ip_sim,ip_con = self.get_vailable_NFVI_ip()
            self.add_NFVInstance(node_id=node,name=f"NVFI-{node}",
                                 cpu=self.substrateTopo.opt_node_attrs_value(node,"capacity_cpu","get"),
                                 ram=self.substrateTopo.opt_node_attrs_value(node,"capacity_ram","get"),
                                 rom=1,
                                 switch_container_handle=self.node_switch_map[node] if self.containernet_handle != None else None,
                                 ip=ip_sim,
                                 ip_control=ip_con)

    def get_vailable_NFVI_ip(self):
        if self.containernet_handle != None:
            index = 1
            while True:
                ip_sim = f"{self.ip_prefix}{index}.0"
                if ip_sim not in self.ips_assigned:
                    self.ips_assigned.add(ip_sim)
                    break
                index += 1
                if index > 255:
                    raise ValueError(f"No available SIM IP for NFV-VIM")
            
            # index = 1 # make sure the control IP used the same index as the SIM IP
            while True:
                ip_con = f"{self.ip_control_prefix}{index}.0"
                if ip_con not in self.ips_control_assigned:
                    self.ips_control_assigned.add(ip_con)
                    break
                index += 1
                if index > 255:
                    raise ValueError(f"No available SIM IP for NFV-VIM")
                
            return ip_sim,ip_con
        else:
            return '0.0.0.0','0.0.0.0'


    def add_NFVInstance(self,node_id,name,cpu:float,ram:float,rom:float,
                         switch_container_handle:Switch = None,ip=None,ip_control=None,port=None):
        nfv_instance = NfvInstance(node_id,name,cpu,ram,rom,switch_container_handle,ip,ip_control,port)
        self.nfv_instance_group[node_id] = nfv_instance
    

    def del_NFVInstance(self,node_id):
        if node_id in self.nfv_instance_group:
            del self.nfv_instance_group[node_id]
    

    def deploy_VNF_on_NFVI(self,vnf_em:VnfEm,NFVI_node_id):
        nfv_instance: NfvInstance = self.nfv_instance_group.get(NFVI_node_id, None)
        if nfv_instance != None:
            nfv_instance.deploy_VNF(vnf_em,containernet_handle=self.containernet_handle)

            self.substrateTopo.opt_node_attrs_value(NFVI_node_id,'remain_cpu','decrease',vnf_em.vnf_cpu)
            self.substrateTopo.opt_node_attrs_value(NFVI_node_id,'remain_ram','decrease',vnf_em.vnf_ram)
            # self.substrateTopo.opt_node_attrs_value(NFVI_node_id,'remain_rom','decrease',vnf_em.vnf_rom)

            return True
        return False
    

    def undeploy_VNF_on_NFVI(self,vnf_em_name:str,NFVI_node_id):
        nfv_instance: NfvInstance = self.nfv_instance_group.get(NFVI_node_id, None)
        if nfv_instance != None:
            if vnf_em_name in nfv_instance.get_deployed_vnfs():
                vnf_em = [vnf_em for vnf_em in nfv_instance.deployed_vnf if vnf_em.vnf_name == vnf_em_name]
                nfv_instance.undeploy_VNF(vnf_em[0],containernet_handle=self.containernet_handle)

                self.substrateTopo.opt_node_attrs_value(NFVI_node_id,'remain_cpu','increase',vnf_em[0].vnf_cpu)
                self.substrateTopo.opt_node_attrs_value(NFVI_node_id,'remain_ram','increase',vnf_em[0].vnf_ram)
                # self.substrateTopo.opt_node_attrs_value(NFVI_node_id,'remain_rom','increase',vnf_em[0].vnf_rom)

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
                 switch_container_handle:'Switch' = None,ip=None,ip_control=None,port=None):
        self.node_id = node_id
        self.name = name
        self.cpu_capacity = cpu
        self.cpu_remain = cpu
        self.ram_capacity = ram
        self.ram_remain = ram
        self.rom_capacity = rom
        self.rom_remain = rom

        self.switch_container_handle = switch_container_handle
        self.ip = ip
        self.ips_assigned: set[str] = set()
        self.ip_control = ip_control
        self.ips_control_assigned: set[str] = set()
        self.port = port

        self.deployed_vnf: list[VnfEm] = []
    
    def deploy_VNF(self,vnf_em:VnfEm,containernet_handle:Containernet=None):
        if containernet_handle != None:
            vnf_em.vnf_ip,vnf_em.vnf_ip_control = self.get_vailable_vnf_ip()
            print(f"Deploy {vnf_em.vnf_name} on {self.name} with IP {vnf_em.vnf_ip} and control IP {vnf_em.vnf_ip_control}")
            vnf_em.ready()
            vnf_em.vnf_container_handle = containernet_handle.addDocker(vnf_em.vnf_name, ip=vnf_em.vnf_ip, 
                                                                        dcmd=vnf_em.vnf_cmd, dimage=vnf_em.vnf_img)
            containernet_handle.addLink(vnf_em.vnf_container_handle, self.switch_container_handle)
            vnf_em.config_network()

        self.deployed_vnf.append(vnf_em)
        self.cpu_remain -= vnf_em.vnf_cpu
        self.ram_remain -= vnf_em.vnf_ram
        self.rom_remain -= vnf_em.vnf_rom
    
    def undeploy_VNF(self,vnf_em:VnfEm,containernet_handle:Containernet=None):
        self.deployed_vnf.remove(vnf_em)
        self.cpu_remain += vnf_em.vnf_cpu
        self.ram_remain += vnf_em.vnf_ram
        self.rom_remain += vnf_em.vnf_rom
        
    def get_deployed_vnfs(self):
        return [vnf_em.vnf_name for vnf_em in self.deployed_vnf]
        
    def get_vailable_vnf_ip(self):
        if self.switch_container_handle != None:
            ip_prefix = self.ip[0:-1]
            index = 1
            while True:
                ip_sim = f"{ip_prefix}{index}"
                if ip_sim not in self.ips_assigned:
                    self.ips_assigned.add(ip_sim)
                    break
                index += 1
                if index > 255:
                    raise ValueError(f"No available SIM IP for {self.name}")
            
            ip_prefix = self.ip_control[0:-1]
            # index = 1 # make sure the control IP used the same index as the SIM IP
            while True:
                ip_con = f"{ip_prefix}{index}"
                if ip_con not in self.ips_control_assigned:
                    self.ips_control_assigned.add(ip_con)
                    break
                index += 1
                if index > 255:
                    raise ValueError(f"No available CON IP for {self.name}")
            
            return ip_sim,ip_con
        else:
            return '0.0.0.0','0.0.0.0'

    