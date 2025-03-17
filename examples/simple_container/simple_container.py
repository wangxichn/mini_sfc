#Anaconda/envs/minisfc python3.10
# -*- coding: utf-8 -*-
'''
simple_container.py
=====================

.. module:: simple_container
  :platform: Windows, Linux
  :synopsis: Module for Service Function Chain (SFC) deployment and simulation.

.. moduleauthor:: CRC1109-WangXi

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



from minisfc.topo import SubstrateTopo,ServiceTopo
from minisfc.net import Minisfc
from minisfc.trace import TRACER
from minisfc.mano.vnfm import VnfManager, VnfEm
from minisfc.mano.uem import UeManager, Ue
from minisfc.util import DataAnalysis, RunCommand

from custom.fixedSolver import FixedSolver

import numpy as np
import code

# region 定义基底网络组 ---------------------------------------------------

topoTimeList = [0.0]
topoAdjMatDict = {0.0:np.array([[1,1,0,0],
                                [1,1,1,0],
                                [0,1,1,1],
                                [0,0,1,1]])}
topoWeightMatDict = {0.0:np.array([ [0,  10, 0,  0],
                                    [10, 0,  10, 0],
                                    [0,  10, 0,  10],
                                    [0,  0,  10, 0]])}
topoNodeResourceDict = {(0.0,'cpu'):[2,2,2,2],
                        (0.0,'ram'):[500,500,500,500]}
topoLinkResourceDict = {(0.0,'band'):np.array([ [10,10,0,0],
                                                [10,10,10,0],
                                                [0,10,10,10],
                                                [0,0,10,10]])}

substrateTopo = SubstrateTopo(topoTimeList,topoAdjMatDict,topoWeightMatDict,topoNodeResourceDict,topoLinkResourceDict)

# endregion

# region 定义服务功能链组 --------------------------------------------------

sfcIdList = [0]                             # sfc 请求的id
sfcLifeTimeDict = {0:[5,25]}                # sfc 生命周期
endPointDict = {0:[2,3]}                    # sfc 端点部署位置限制（即强制vnf_gnb部署位置）
arriveFunParamDict = {0:[1.0,2.0]}          # sfc 业务参数
vnfRequstDict = {0:[2,0,2]}                 # sfc 请求的vnf列表
qosRequesDict = {0:[100]}                   # sfc 请求的qos列表（目前只有时延）

serviceTopo = ServiceTopo(sfcIdList,sfcLifeTimeDict,endPointDict,arriveFunParamDict,vnfRequstDict,qosRequesDict)

# endregion

# region 定义MANO中VNF库 --------------------------------------------------

# MANO中可供部署的vnf库
nfvManager = VnfManager()
template_str = "python run_command.py --vnf_name=$vnf_name --vnf_type=$vnf_type --vnf_ip=$vnf_ip --vnf_port=$vnf_port --vnf_cpu=$vnf_cpu --vnf_ram=$vnf_ram --vnf_rom=$vnf_rom"

vnfEm_template = VnfEm(**{'vnf_id':0,'vnf_unit':3,'vnf_factor':1.0,'vnf_cpu':0.15,'vnf_ram':100,
                          'vnf_type':'vnf_matinv','vnf_img':'vnfserver:latest','vnf_cmd':template_str,'vnf_port':5000})
nfvManager.add_vnf_into_pool(vnfEm_template)
vnfEm_template = VnfEm(**{'vnf_id':1,'vnf_unit':2,'vnf_factor':1.0,'vnf_cpu':0.15,'vnf_ram':100,
                          'vnf_type':'vnf_matprint','vnf_img':'vnfserver:latest','vnf_cmd':template_str,'vnf_port':5000})
nfvManager.add_vnf_into_pool(vnfEm_template)
vnfEm_template = VnfEm(**{'vnf_id':2,'vnf_unit':1,'vnf_factor':1.0,'vnf_cpu':0.15,'vnf_ram':100,
                          'vnf_type':'vnf_gnb','vnf_img':'vnfserver:latest','vnf_cmd':template_str,'vnf_port':5000})
nfvManager.add_vnf_into_pool(vnfEm_template)

nfvManager.add_vnf_service_into_pool(0,1,**{"band":0.5})
nfvManager.add_vnf_service_into_pool(1,0,**{"band":0.5})
nfvManager.add_vnf_service_into_pool(0,2,**{"band":0.5})
nfvManager.add_vnf_service_into_pool(2,0,**{"band":0.5})
nfvManager.add_vnf_service_into_pool(1,2,**{"band":0.5})
nfvManager.add_vnf_service_into_pool(2,1,**{"band":0.5})

# endregion

# region 定义SFC的用户业务类型 ---------------------------------------------
ueManager = UeManager()
template_str = "python run_command.py --ue_name=$ue_name --ue_type=$ue_type --ue_ip=$ue_ip --ue_port=$ue_port"

ue_template = Ue(**{'ue_id':0,'ue_type':'ue_post','ue_img':'ueserver:latest','ue_cmd':template_str,'ue_port':8000})
ueManager.add_ue_into_pool(ue_template)
ue_template = Ue(**{'ue_id':1,'ue_type':'ue_print','ue_img':'ueserver:latest','ue_cmd':template_str,'ue_port':8000})
ueManager.add_ue_into_pool(ue_template)

ueManager.add_ue_service_into_pool(0,1,**{"req_delay":1}) # set the delay (1s) of the request from ue0 to ue1

# endregion

# region 定义SFC部署解决方案 -----------------------------------------------

sfcSolver = FixedSolver(substrateTopo,serviceTopo)

# endregion

# region 定义部署结果追踪器 -------------------------------------------------

netTraceFile = f'multisfc_staticopo_{sfcSolver.__class__.__name__}_{TRACER.get_time_stamp()}.csv'
TRACER.set(netTraceFile)

# endregion

# region 将各组件代入仿真引擎 ------------------------------------------------

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver,ueManager=ueManager,use_container=True)

try:
    net.start()
    # net.addCLI()
    net.stop()
except Exception as e:
    net.stop()
    # runCommand = RunCommand()
    # runCommand.clear_container()
    TRACER.delete()
    raise e
    
# endregion


