
from minisfc.topo import SubstrateTopo,ServiceTopo
from minisfc.mano.vnfm import VnfManager
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

substrateTopo_pklname = "SubstrateTopo_20240903083515877.pkl"
serviceTopo_pklname = "ServiceTopo_20240903083515970.pkl"
nfvManager_pklname = "NfvManager_20240903083515981.pkl"

with open(substrateTopo_pklname, "rb") as file:
    substrateTopo = pickle.load(file)
with open(serviceTopo_pklname, "rb") as file:
    serviceTopo = pickle.load(file)
with open(nfvManager_pklname, "rb") as file:
    nfvManager = pickle.load(file)

sfcSolver = netcalOptSolver(substrateTopo,serviceTopo)
sfcSolver.loadParam()

# netTraceFile = f'netcal_statictopo_{sfcSolver.__class__.__name__}_{TRACER.get_time_stamp()}.csv'
netTraceFile = f'netcal_statictopo_{sfcSolver.__class__.__name__}_temp.csv'
TRACER.set(netTraceFile)

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver)
net.start()
net.stop()

sfcSolver.saveParam()

DataAnalysis.getResult(netTraceFile)

# code.interact(banner="",local=locals())
