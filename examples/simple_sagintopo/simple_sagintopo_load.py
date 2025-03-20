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

from minisfc.trace import TRACE_RESULT, TRACE_NFVI, Trace
from minisfc.util import DataAnalysis
import pickle

substrateTopo_pklname = "SubstrateTopo_20250319182626597.pkl"
serviceTopo_pklname = "ServiceTopo_20250319182626597.pkl"
vnfManager_pklname = "VnfManager_20250319182626597.pkl"

# region step1: define substrate topologies--------------------------------------------

from minisfc.topo import SubstrateTopo

with open(substrateTopo_pklname, "rb") as file:
    substrateTopo: SubstrateTopo = pickle.load(file)

# endregion

# region step2: define sfc topologies------------------------------------------------

from minisfc.topo import ServiceTopo

with open(serviceTopo_pklname, "rb") as file:
    serviceTopo: ServiceTopo = pickle.load(file)

#  endregion

# region step3: define vnf manager--------------------------------------------------

from minisfc.mano.vnfm import VnfManager, VnfEm

with open(vnfManager_pklname, "rb") as file:
    nfvManager = pickle.load(file)

# endregion

# region step4: define sfc solver-----------------------------------------------------

from minisfc.solver import RadomSolver, GreedySolver
from custom.psoSolver import PsoSolver

sfcSolver = RadomSolver(substrateTopo,serviceTopo)
sfcSolver.loadParam()

# endregion

SIMULATION_ID = Trace.get_time_stamp()

TraceResultFile = f'{TRACE_RESULT.__class__.__name__}_{sfcSolver.__class__.__name__}_{SIMULATION_ID}.csv'
TRACE_RESULT.set(TraceResultFile)
TraceNfviFile = f'{TRACE_NFVI.__class__.__name__}_{sfcSolver.__class__.__name__}_{SIMULATION_ID}.csv'
TRACE_NFVI.set(TraceNfviFile)

# region step5: define minisfc simulation----------------------------------------------

from minisfc.net import Minisfc

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver)
net.start()
net.stop()

sfcSolver.saveParam()

DataAnalysis.getResult(TraceResultFile)

# code.interact(banner="",local=locals())

# endregion