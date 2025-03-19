#Anaconda/envs/minisfc python
# -*- coding: utf-8 -*-
'''
simple_sagingtopo.py
=====================

.. module:: simple_sagingtopo
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

- Version 1.0 (2025/03/19): Initial version

'''

from minisfc.trace import TRACER
from minisfc.util import NumberGen, DataAnalysis, JsonReader
import numpy as np
import pickle
import random
import os

SIMULATION_ID = TRACER.get_time_stamp()

# region step1: define substrate topologies--------------------------------------------

from minisfc.topo import SubstrateTopo

jsondir = 'SSG-Json-RawData'
jsonfiles = [os.path.join(jsondir, file) for file in os.listdir(jsondir)]

jsonReader = JsonReader(jsonfiles[0])
topoNodeNames = jsonReader.all_node_list
topoNodeNum_Sat = jsonReader.sat_num
topoNodeNum_Base = jsonReader.base_num
topoNodeNum_Uav = jsonReader.uav_num
# topoAdjMat = jsonReader.getAdjacencyMat()
# topoWeightMat = jsonReader.getWeightMat()

topoSize = len(topoNodeNames)
topoTimeList = list(np.arange(0.0,600.0,10.0))
topoAdjMatDict = {topoTime:JsonReader(jsonfiles[i]).getAdjacencyMat() for i,topoTime in enumerate(topoTimeList)}
topoWeightMatDict = {topoTime:JsonReader(jsonfiles[i]).getWeightMat() for i,topoTime in enumerate(topoTimeList)}
topoNodeResourceDict_cpu = {(topoTime,'cpu'):NumberGen.getVector(topoSize,**{'distribution':'uniform','dtype':'int','low':100,'high':500}) # unit conversion Mb
                            for topoTime in topoTimeList}
topoNodeResourceDict_ram = {(topoTime,'ram'):NumberGen.getVector(topoSize,**{'distribution':'uniform','dtype':'int','low':500,'high':500})*1000 # unit conversion Gb2Mb
                            for topoTime in topoTimeList}
topoNodeResourceDict = {**topoNodeResourceDict_cpu,**topoNodeResourceDict_ram}

topoLinkResourceMat_Sat = NumberGen.getMatrix(topoNodeNum_Sat,**{'type':'symmetric','dtype':'int','low':100,'high':1000}) # unit conversion Mb
topoLinkResourceMat_Other = NumberGen.getMatrix(len(topoNodeNames),**{'type':'symmetric','dtype':'int','low':50,'high':300}) # unit conversion Mb
topoLinkResourceMat_Other[0:topoNodeNum_Sat,0:topoNodeNum_Sat] = topoLinkResourceMat_Sat
topoLinkResourceDict = {(topoTime,'band'):topoLinkResourceMat_Other+np.eye(topoSize,dtype=int)*20*1000 for topoTime in topoTimeList}  # unit conversion Gb2Mb

substrateTopo = SubstrateTopo(topoTimeList,topoAdjMatDict,topoWeightMatDict,topoNodeResourceDict,topoLinkResourceDict)

with open(f"{substrateTopo.__class__.__name__}_{SIMULATION_ID}.pkl", "wb") as file:
    pickle.dump(substrateTopo, file)

# endregion

# region step2: define sfc topologies------------------------------------------------

from minisfc.topo import ServiceTopo

sfcNum = 300
sfcVnfTypeNum = 10
sfcIdList = [i for i in range(sfcNum)]
sfcVnfIdList = [i for i in range(sfcVnfTypeNum)]

sfcNum_URLLC = int(sfcNum*(2/8))
sfcNum_mMTC = int(sfcNum*(5/8))
sfcNum_eMBB = sfcNum-(sfcNum_URLLC+sfcNum_mMTC)

sfcArriveTime = np.cumsum(NumberGen.getVector(sfcNum,**{'distribution':'possion','dtype':'float','lam':0.55,'reciprocal':True}))
sfcLifeLength = NumberGen.getVector(sfcNum,**{'distribution':'uniform','dtype':'float','low':5,'high':60})
sfcLifeTimeDict = {sfcIdList[i]:[sfcArriveTime[i],sfcArriveTime[i]+sfcLifeLength[i]] for i in range(sfcNum)}
sfcEndPointDict = {sfcIdList[i]:[random.sample(range(topoSize),1)[0],random.sample(range(topoSize),1)[0]] for i in range(sfcNum)}

sfcLatencyRequest_URLLC = NumberGen.getVector(sfcNum_URLLC,**{'distribution':'uniform','dtype':'float','low':0.1,'high':0.150})
sfcLatencyRequest_mMTC = NumberGen.getVector(sfcNum_mMTC,**{'distribution':'uniform','dtype':'float','low':0.1,'high':0.300})
sfcLatencyRequest_eMBB = NumberGen.getVector(sfcNum_eMBB,**{'distribution':'uniform','dtype':'float','low':0.1,'high':0.400})
sfcLatencyRequest = np.concatenate((sfcLatencyRequest_URLLC,sfcLatencyRequest_mMTC,sfcLatencyRequest_eMBB))


sfcVnfNum = NumberGen.getVector(sfcNum,**{'distribution':'uniform','dtype':'int','low':5,'high':10})
sfcVnfRequstDict = {sfcIdList[i]:random.sample(sfcVnfIdList,sfcVnfNum[i]) for i in range(sfcNum)}
sfcQosRequestDict = {sfcIdList[i]:[sfcLatencyRequest[i]] for i in range(sfcNum)}

serviceTopo = ServiceTopo(sfcIdList,sfcLifeTimeDict,sfcEndPointDict,sfcVnfRequstDict,sfcQosRequestDict)
with open(f"{serviceTopo.__class__.__name__}_{SIMULATION_ID}.pkl", "wb") as file:
    pickle.dump(serviceTopo, file)

#  endregion

# region step3: define vnf manager--------------------------------------------------

from minisfc.mano.vnfm import VnfManager, VnfEm

vnfRequstCPU = NumberGen.getVector(sfcVnfTypeNum,**{'distribution':'uniform','dtype':'int','low':1,'high':10})
vnfRequstRAM = NumberGen.getVector(sfcVnfTypeNum,**{'distribution':'uniform','dtype':'int','low':1,'high':10})
vnfRequstBAND = NumberGen.getMatrix(sfcVnfTypeNum,**{'type':'symmetric','dtype':'int','low':10,'high':100})
nfvManager = VnfManager()
for i in range(sfcVnfTypeNum):
    vnfEm_template = VnfEm(**{'vnf_id':i,'vnf_cpu':vnfRequstCPU[i],'vnf_ram':vnfRequstRAM[i]})
    nfvManager.add_vnf_into_pool(vnfEm_template)
for i in range(sfcVnfTypeNum):
    for j in range(sfcVnfTypeNum):
        nfvManager.add_vnf_service_into_pool(i,j,**{"band":vnfRequstBAND[i,j]})

with open(f"{nfvManager.__class__.__name__}_{SIMULATION_ID}.pkl", "wb") as file:
    pickle.dump(nfvManager, file)

# endregion

# region step4: define sfc solver-----------------------------------------------------

from minisfc.solver import RadomSolver, GreedySolver
from custom.psoSolver import PsoSolver

sfcSolver = PsoSolver(substrateTopo,serviceTopo)
sfcSolver.loadParam()

# endregion

netTraceFile = f'simple_sagintopo_{sfcSolver.__class__.__name__}_{TRACER.get_time_stamp()}.csv'
TRACER.set(netTraceFile)

# region step5: define minisfc simulation----------------------------------------------

from minisfc.net import Minisfc

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver)
net.start()
net.stop()

sfcSolver.saveParam()

DataAnalysis.getResult(netTraceFile)

# code.interact(banner="",local=locals())

# endregion