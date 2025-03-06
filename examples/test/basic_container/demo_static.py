#Anaconda/envs/minisfc python
# -*- coding: utf-8 -*-
'''
demo.py
=========

.. module:: demo
  :platform: Linux
  :synopsis: This is an example how to simulate a vnf server environment.

.. moduleauthor:: Wang Xi

Introduction
-----------

This module implements a basic vnf server environment, primarily used in vnf server applications. It provides the following features:

- Uses a vnf server container to render vnfs.
- Supports basic vnf control operations.

Version
-------

- Version 1.0 (2025/03/06): Initial version

'''

from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel

setLogLevel('info')

net = Containernet(controller=Controller)

net.addController('c0')

# region Adding vnf server container ------------------------- 1

info('*** Adding vnf server container\n')

vnf_1_info = {'vnf_name':'vnf_1','vnf_type':'vnf_matinv','vnf_ip':'10.0.0.11','vnf_port':'5000',
                'vnf_cpu':'0.5', 'vnf_ram':'0.2', 'vnf_rom':'10', 'control_ip':'172.17.0.11'}
vnf_2_info = {'vnf_name':'vnf_2','vnf_type':'vnf_matprint','vnf_ip':'10.0.0.12','vnf_port':'5000',
                'vnf_cpu':'0.2', 'vnf_ram':'0.1', 'vnf_rom':'20', 'control_ip':'172.17.0.12'}
vnf_3_info = {'vnf_name':'vnf_3','vnf_type':'vnf_gnb','vnf_ip':'10.0.0.13','vnf_port':'5000',
                'vnf_cpu':'0.3', 'vnf_ram':'0.2', 'vnf_rom':'30', 'control_ip':'172.17.0.13'}
vnf_4_info = {'vnf_name':'vnf_4','vnf_type':'vnf_gnb','vnf_ip':'10.0.0.14','vnf_port':'5000',
                'vnf_cpu':'0.3', 'vnf_ram':'0.2', 'vnf_rom':'30', 'control_ip':'172.17.0.14'}

vnf_1 = net.addDocker(vnf_1_info['vnf_name'], ip=vnf_1_info['vnf_ip'], 
                       dcmd=f"""python run_command.py --vnf_name={vnf_1_info['vnf_name']} 
                                --vnf_type={vnf_1_info['vnf_type']} --vnf_ip={vnf_1_info['vnf_ip']} --vnf_port={vnf_1_info['vnf_port']} 
                                --vnf_cpu={vnf_1_info['vnf_cpu']} --vnf_ram={vnf_1_info['vnf_ram']} 
                                --vnf_rom={vnf_1_info['vnf_rom']}""", 
                       dimage="vnfserver:latest")
vnf_1.cmd(f"ifconfig eth0 {vnf_1_info['control_ip']} netmask 255.0.0.0 up")

vnf_2 = net.addDocker(vnf_2_info['vnf_name'], ip=vnf_2_info['vnf_ip'], 
                       dcmd=f"""python run_command.py --vnf_name={vnf_2_info['vnf_name']} 
                                --vnf_type={vnf_2_info['vnf_type']} --vnf_ip={vnf_2_info['vnf_ip']} --vnf_port={vnf_2_info['vnf_port']} 
                                --vnf_cpu={vnf_2_info['vnf_cpu']} --vnf_ram={vnf_2_info['vnf_ram']} 
                                --vnf_rom={vnf_2_info['vnf_rom']}""", 
                       dimage="vnfserver:latest")
vnf_2.cmd(f"ifconfig eth0 {vnf_2_info['control_ip']} netmask 255.0.0.0 up")

vnf_3 = net.addDocker(vnf_3_info['vnf_name'], ip=vnf_3_info['vnf_ip'], 
                       dcmd=f"""python run_command.py --vnf_name={vnf_3_info['vnf_name']} 
                                --vnf_type={vnf_3_info['vnf_type']} --vnf_ip={vnf_3_info['vnf_ip']} --vnf_port={vnf_3_info['vnf_port']} 
                                --vnf_cpu={vnf_3_info['vnf_cpu']} --vnf_ram={vnf_3_info['vnf_ram']} 
                                --vnf_rom={vnf_3_info['vnf_rom']}""", 
                       dimage="vnfserver:latest")
vnf_3.cmd(f"ifconfig eth0 {vnf_3_info['control_ip']} netmask 255.0.0.0 up")

vnf_4 = net.addDocker(vnf_4_info['vnf_name'], ip=vnf_4_info['vnf_ip'], 
                       dcmd=f"""python run_command.py --vnf_name={vnf_4_info['vnf_name']} 
                                --vnf_type={vnf_4_info['vnf_type']} --vnf_ip={vnf_4_info['vnf_ip']} --vnf_port={vnf_4_info['vnf_port']} 
                                --vnf_cpu={vnf_4_info['vnf_cpu']} --vnf_ram={vnf_4_info['vnf_ram']} 
                                --vnf_rom={vnf_4_info['vnf_rom']}""", 
                       dimage="vnfserver:latest")
vnf_4.cmd(f"ifconfig eth0 {vnf_4_info['control_ip']} netmask 255.0.0.0 up")

# endregion

# region Adding ue server container  ------------------------- 2

info('*** Adding ue server container\n')

ue_2_info = {'ue_name':'ue_2','ue_type':'ue_print','ue_ip':'10.0.0.102','ue_port':'8002',
             'control_ip':'172.17.0.102', 'ue_aim':None}
ue_1_info = {'ue_name':'ue_1','ue_type':'ue_post','ue_ip':'10.0.0.101','ue_port':'8001',
             'control_ip':'172.17.0.101', 'ue_aim':ue_2_info}
    
ue_1 = net.addDocker(ue_1_info['ue_name'], ip=ue_1_info['ue_ip'], 
                     dimage="ueserver:latest")
ue_1.cmd(f"ifconfig eth0 {ue_1_info['control_ip']} netmask 255.0.0.0 up")

ue_2 = net.addDocker(ue_2_info['ue_name'], ip=ue_2_info['ue_ip'], 
                     dimage="ueserver:latest")
ue_2.cmd(f"ifconfig eth0 {ue_2_info['control_ip']} netmask 255.0.0.0 up")

# endregion

# region Adding links between vnf/ue server and switch ------------------------- 3

info('*** Setup network\n')
s1 = net.addSwitch('s1')
s2 = net.addSwitch('s2')
s3 = net.addSwitch('s3')
s4 = net.addSwitch('s4')

net.addLink(s1, s2, cls=TCLink, delay='10ms', bw=1)
net.addLink(s2, s3, cls=TCLink, delay='10ms', bw=1)
net.addLink(s3, s4, cls=TCLink, delay='10ms', bw=1)

net.addLink(vnf_1, s1)
net.addLink(vnf_2, s2)
net.addLink(vnf_3, s3)
net.addLink(vnf_4, s4)

net.addLink(ue_1, s3, cls=TCLink, delay='100ms', bw=1)
net.addLink(ue_2, s4, cls=TCLink, delay='100ms', bw=1)

# endregion

net.start()

info('*** Starting to execute commands\n')
CLI(net)

net.stop()
