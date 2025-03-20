#Anaconda/envs/minisfc python3.10
# -*- coding: utf-8 -*-
'''
simple_container.py
=====================

.. module:: simple_container
  :platform: Linux
  :synopsis: Module for Service Function Chain (SFC) deployment and simulation.

.. moduleauthor:: WangXi

Introduction
-----------

This module implements Service Function Chain (SFC) deployment functionality, primarily 
used in network function virtualization (NFV) applications. It provides the following features:

- Defines substrate and service topologies for SFC deployment.
- Manages a virtual network function (VNF) pool using a Virtual Network Function Manager (VNFM).
- Manages user equipment (UE) types and services using a User Equipment Manager (UEM).
- Implements a fixed solver for SFC deployment.
- Tracks and logs deployment results using a tracer.

Version
-------

- Version 1.0 (2025/03/14): Initial version

'''

from minisfc.trace import TRACE_RESULT, TRACE_NFVI, Trace
import numpy as np
import pickle

SIMULATION_ID = Trace.get_time_stamp()

# region step1: define substrate topologies--------------------------------------------

from minisfc.topo import SubstrateTopo

topoTimeList = [0.0]
topoAdjMatDict = {0.0:np.array([[1,1,0],
                                [1,1,1],
                                [0,1,1]])}
topoWeightMatDict = {0.0:np.array([[0,20,0], # delay ms
                                   [20,0,10],
                                   [0,10,0]])}
topoNodeResourceDict = {(0.0,'cpu'):[2,4,2], # cores
                        (0.0,'ram'):[256,512,256]} # Memmory MB
topoLinkResourceDict = {(0.0,'band'):np.array([[100,100,0], # bw Mbps
                                               [100,100,100],
                                               [0,100,100]])}
substrateTopo = SubstrateTopo(topoTimeList,topoAdjMatDict,topoWeightMatDict,
                              topoNodeResourceDict,topoLinkResourceDict)

with open(f"{substrateTopo.__class__.__name__}_{SIMULATION_ID}.pkl", "wb") as file:
    pickle.dump(substrateTopo, file)

# endregion

# region step2: define sfc topologies------------------------------------------------

from minisfc.topo import ServiceTopo

sfcIdList = [0,1]                             # sfc 请求的id
sfcLifeTimeDict = {0:[5,25],
                   1:[10,50]}                # sfc 生命周期
endPointDict = {0:[0,2],
                1:[0,1]}                    # sfc 端点部署位置限制（即强制vnf_gnb部署位置）
vnfRequstDict = {0:[2,0,2],
                 1:[2,0,2]}                 # sfc 请求的vnf列表
qosRequesDict = {0:[100],
                 1:[100]}                   # sfc 请求的qos列表（目前只有时延）

serviceTopo = ServiceTopo(sfcIdList,sfcLifeTimeDict,endPointDict,vnfRequstDict,qosRequesDict)
with open(f"{serviceTopo.__class__.__name__}_{SIMULATION_ID}.pkl", "wb") as file:
    pickle.dump(serviceTopo, file)

# endregion

# region step3: define vnf manager--------------------------------------------------

from minisfc.mano.vnfm import VnfManager,VnfEm

nfvManager = VnfManager()
template_str = "python run_command.py --vnf_name=$vnf_name --vnf_type=$vnf_type --vnf_ip=$vnf_ip --vnf_port=$vnf_port --vnf_cpu=$vnf_cpu --vnf_ram=$vnf_ram --vnf_rom=$vnf_rom"

vnfEm_template = VnfEm(**{'vnf_id':0,'vnf_cpu':0.2,'vnf_ram':64,
                          'vnf_type':'vnf_matinv','vnf_img':'vnfserver:latest','vnf_cmd':template_str,'vnf_port':5000})
nfvManager.add_vnf_into_pool(vnfEm_template)
vnfEm_template = VnfEm(**{'vnf_id':1,'vnf_cpu':0.15,'vnf_ram':64,
                          'vnf_type':'vnf_matprint','vnf_img':'vnfserver:latest','vnf_cmd':template_str,'vnf_port':5000})
nfvManager.add_vnf_into_pool(vnfEm_template)
vnfEm_template = VnfEm(**{'vnf_id':2,'vnf_cpu':0.15,'vnf_ram':64,
                          'vnf_type':'vnf_gnb','vnf_img':'vnfserver:latest','vnf_cmd':template_str,'vnf_port':5000})
nfvManager.add_vnf_into_pool(vnfEm_template)

nfvManager.add_vnf_service_into_pool(2,0,**{"band":20})
nfvManager.add_vnf_service_into_pool(0,2,**{"band":20})

with open(f"{nfvManager.__class__.__name__}_{SIMULATION_ID}.pkl", "wb") as file:
    pickle.dump(nfvManager, file)

# endregion

# region step4: define ue manager--------------------------------------------------

from minisfc.mano.uem import UeManager, Ue

ueManager = UeManager()
template_str = "python run_command.py --ue_name=$ue_name --ue_type=$ue_type --ue_ip=$ue_ip --ue_port=$ue_port"

ue_template = Ue(**{'ue_id':0,'ue_type':'ue_post','ue_img':'ueserver:latest','ue_cmd':template_str,'ue_port':8000})
ueManager.add_ue_into_pool(ue_template)
ue_template = Ue(**{'ue_id':1,'ue_type':'ue_print','ue_img':'ueserver:latest','ue_cmd':template_str,'ue_port':8000})
ueManager.add_ue_into_pool(ue_template)

ueManager.add_ue_service_into_pool(0,1,**{"req_delay":0.1}) # set the delay (1s) of the request from ue0 to ue1

with open(f"{ueManager.__class__.__name__}_{SIMULATION_ID}.pkl", "wb") as file:
    pickle.dump(ueManager, file)

# endregion

# region step5: define sfc solver-----------------------------------------------------

from minisfc.solver import RadomSolver, GreedySolver
from custom.psoSolver import PsoSolver

sfcSolver = RadomSolver(substrateTopo,serviceTopo)

# endregion

TraceResultFile = f'{TRACE_RESULT.__class__.__name__}_{sfcSolver.__class__.__name__}_{SIMULATION_ID}.csv'
TRACE_RESULT.set(TraceResultFile)
TraceNfviFile = f'{TRACE_NFVI.__class__.__name__}_{sfcSolver.__class__.__name__}_{SIMULATION_ID}.csv'
TRACE_NFVI.set(TraceNfviFile)

# region step6: define minisfc simulation----------------------------------------------

from minisfc.net import Minisfc

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver,ueManager=ueManager,use_container=True)

try:
    net.start()
    # net.addCLI()
    net.stop()
except Exception as e:
    net.stop()
    # runCommand = RunCommand()
    # runCommand.clear_container()
    TRACE_RESULT.delete()
    TRACE_NFVI.delete()
    raise e
    
# endregion


