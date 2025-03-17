
from minisfc.net import Minisfc
from minisfc.trace import TRACER
from minisfc.util import DataAnalysis
from custom.netcalSolver import netcalPsoSolver, netcalOptSolver, netcalSfcpSolver, netcalRandomSolver, netcalGreedySolver
import numpy as np
np.seterr(over='warn')
import pickle
import code

substrateTopo_pklname = "SubstrateTopo_20250314101628056.pkl"
serviceTopo_pklname = "ServiceTopo_20250314101628058.pkl"
vnfManager_pklname = "VnfManager_20250314101628060.pkl"

with open(substrateTopo_pklname, "rb") as file:
    substrateTopo = pickle.load(file)
with open(serviceTopo_pklname, "rb") as file:
    serviceTopo = pickle.load(file)
with open(vnfManager_pklname, "rb") as file:
    nfvManager = pickle.load(file)

sfcSolver = netcalPsoSolver(substrateTopo,serviceTopo)
sfcSolver.loadParam()

netTraceFile = f'netcal_statictopo_{sfcSolver.__class__.__name__}_{TRACER.get_time_stamp()}.csv'
TRACER.set(netTraceFile)

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver)
net.start()
net.stop()

sfcSolver.saveParam()

DataAnalysis.getResult(netTraceFile)

# code.interact(banner="",local=locals())
