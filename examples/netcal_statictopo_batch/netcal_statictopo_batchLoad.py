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

substrateTopo_pklname = "SubstrateTopo_20240901090234816.pkl"
with open(substrateTopo_pklname, "rb") as file:
    substrateTopo = pickle.load(file)

nfvManager_pklname = "NfvManager_20240901090235086.pkl"
with open(nfvManager_pklname, "rb") as file:
    nfvManager = pickle.load(file)

for sfcNum in range(600,900,100):
    serviceTopo_pklname = f"ServiceTopo_{sfcNum}.pkl"
    with open(serviceTopo_pklname, "rb") as file:
        serviceTopo = pickle.load(file)

    sfcSolver = netcalOptSolver(substrateTopo,serviceTopo)
    sfcSolver.loadParam()

    netTraceFile = f'netcal_statictopo_{sfcSolver.__class__.__name__}_{sfcNum}.csv'
    TRACER.set(netTraceFile)

    net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver)
    net.start()
    net.stop()

    sfcSolver.saveParam()

    DataAnalysis.getResult(netTraceFile)

