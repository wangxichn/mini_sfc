#Anaconda/envs/minisfc python
# -*- coding: utf-8 -*-
'''
simple_dynamictopo.py
=====================

.. module:: simple_dynamictopo
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

from minisfc.trace import TRACE_RESULT, TRACE_NFVI
import numpy as np
import pickle

SIMULATION_ID = TRACE_RESULT.get_time_stamp()

# region step1: define substrate topologies--------------------------------------------

from minisfc.topo import SubstrateTopo

topoTimeList = [0.0,12.0,20.0]
topoAdjMatDict = {0.0:np.array([[1,1,1],
                                  [1,1,1],
                                  [1,1,1]]),
                    12.0:np.array([[1,0,1],
                                  [0,1,1],
                                  [1,1,1]]),
                    20.0:np.array([[1,1,1],
                                  [1,1,0],
                                  [1,0,1]])}
topoWeightMatDict = {0.0:np.array([[0,20,10], # delay ms
                               [20,0,10],
                               [10,10,0]]),
                 12.0:np.array([[0,0,20],
                               [0,0,10],
                               [20,10,0]]),
                 20.0:np.array([[0,30,10],
                               [30,0,0],
                               [10,0,0]])}
topoNodeResourceDict = {(0.0,'cpu'):[2,4,2], # cores
                    (0.0,'ram'):[256,512,256], # Memmory MB
                    (12.0,'cpu'):[2,4,2],
                    (12.0,'ram'):[256,512,256],
                    (20.0,'cpu'):[2,4,2],
                    (20.0,'ram'):[256,512,256],}
topoLinkResourceDict = {(0.0,'band'):np.array([[100,100,100], # bw Mbps
                                           [100,100,100],
                                           [100,100,100]]),
                    (12.0,'band'):np.array([[100,0,100],
                                           [0,100,100],
                                           [100,100,100]]),
                    (20.0,'band'):np.array([[100,100,100],
                                           [100,100,0],
                                           [100,0,100]])}

substrateTopo = SubstrateTopo(topoTimeList,topoAdjMatDict,topoWeightMatDict,
                              topoNodeResourceDict,topoLinkResourceDict)
with open(f"{substrateTopo.__class__.__name__}_{SIMULATION_ID}.pkl", "wb") as file:
    pickle.dump(substrateTopo, file)

# endregion

# region step2: define sfc topologies------------------------------------------------

from minisfc.topo import ServiceTopo

sfcIdList = [0,1,2]
sfcLifeTimeDict = {0:[5,25],
                   1:[10,30],
                   2:[15,35]}
endPointDict = {0:[0,1],
                1:[0,2],
                2:[1,2]}
vnfRequstDict = {0:[0,1,2],
                 1:[0,1],
                 2:[2,1]}
qosRequesDict = {0:[100],
                 1:[100],
                 2:[100]}

serviceTopo = ServiceTopo(sfcIdList,sfcLifeTimeDict,endPointDict,vnfRequstDict,qosRequesDict)
with open(f"{serviceTopo.__class__.__name__}_{SIMULATION_ID}.pkl", "wb") as file:
    pickle.dump(serviceTopo, file)

#  endregion

# region step3: define vnf manager--------------------------------------------------

from minisfc.mano.vnfm import VnfManager,VnfEm

nfvManager = VnfManager()
vnfEm_template = VnfEm(**{'vnf_id':0,'vnf_cpu':0.2,'vnf_ram':64})
nfvManager.add_vnf_into_pool(vnfEm_template)
vnfEm_template = VnfEm(**{'vnf_id':1,'vnf_cpu':0.15,'vnf_ram':64})
nfvManager.add_vnf_into_pool(vnfEm_template)
vnfEm_template = VnfEm(**{'vnf_id':2,'vnf_cpu':0.15,'vnf_ram':64})
nfvManager.add_vnf_into_pool(vnfEm_template)

nfvManager.add_vnf_service_into_pool(0,1,**{"band":20})
nfvManager.add_vnf_service_into_pool(1,2,**{"band":20})
nfvManager.add_vnf_service_into_pool(2,1,**{"band":20})

with open(f"{nfvManager.__class__.__name__}_{SIMULATION_ID}.pkl", "wb") as file:
    pickle.dump(nfvManager, file)

# endregion

# region step4: define sfc solver-----------------------------------------------------

from minisfc.solver import RadomSolver, GreedySolver
from custom.psoSolver import PsoSolver

sfcSolver = RadomSolver(substrateTopo,serviceTopo)

# endregion

TraceResultFile = f'{TRACE_RESULT.__class__.__name__}_{sfcSolver.__class__.__name__}_{SIMULATION_ID}.csv'
TRACE_RESULT.set(TraceResultFile)
TraceNfviFile = f'{TRACE_NFVI.__class__.__name__}_{sfcSolver.__class__.__name__}_{SIMULATION_ID}.csv'
TRACE_NFVI.set(TraceNfviFile)

# region step5: define minisfc simulation----------------------------------------------

from minisfc.net import Minisfc

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver)
net.start()
net.stop()

# endregion
