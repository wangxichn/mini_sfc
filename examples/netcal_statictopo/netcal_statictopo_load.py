import sys
#添加上级目录
sys.path.append("..//..//")
from minisfc.topo import SubstrateTopo,ServiceTopo
from minisfc.mano import NfvManager
from minisfc.solver import RadomSolver, GreedySolver
from minisfc.net import Minisfc
from minisfc.trace import TRACER
from util import NumberGen, TopoGen, DataAnalysis, JsonReader
from custom.psoSolver import PsoSolver
from custom.drlSfcpSolver.drlSfcpSolver import DrlSfcpSolver
from custom.netcalSolver import netcalPsoSolver, netcalOptSolver, netcalSfcpSolver, netcalRandomSolver, netcalGreedySolver
import numpy as np
np.seterr(over='warn')
import pickle
import code
import random

substrateTopo_pklname = "SubstrateTopo_20240628101139388.pkl"
serviceTopo_pklname = "ServiceTopo_20240628101139390.pkl"
nfvManager_pklname = "NfvManager_20240628101139395.pkl"

with open(substrateTopo_pklname, "rb") as file:
    substrateTopo = pickle.load(file)
with open(serviceTopo_pklname, "rb") as file:
    serviceTopo = pickle.load(file)
with open(nfvManager_pklname, "rb") as file:
    nfvManager = pickle.load(file)

sfcSolver = netcalGreedySolver(substrateTopo,serviceTopo)
sfcSolver.loadParam()

netTraceFile = f'netcal_statictopo_{sfcSolver.__class__.__name__}_{TRACER.get_time_stamp()}.csv'
TRACER.set(netTraceFile)

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver)
net.start()
net.stop()

sfcSolver.saveParam()

DataAnalysis.getResult(netTraceFile)

# code.interact(banner="",local=locals())
