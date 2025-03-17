
from minisfc.net import Minisfc
from minisfc.trace import TRACER
from minisfc.util import DataAnalysis
from custom.netcalSolver import netcalPsoSolver, netcalOptSolver, netcalSfcpSolver, netcalRandomSolver, netcalGreedySolver
import numpy as np
np.seterr(over='warn')
import pickle

substrateTopo_pklname = "SubstrateTopo_20250314102544451.pkl"
with open(substrateTopo_pklname, "rb") as file:
    substrateTopo = pickle.load(file)

vnfManager_pklname = "VnfManager_20250314102544588.pkl"
with open(vnfManager_pklname, "rb") as file:
    nfvManager = pickle.load(file)

for sfcNum in range(300,900,100):
    serviceTopo_pklname = f"ServiceTopo_{sfcNum}.pkl"
    with open(serviceTopo_pklname, "rb") as file:
        serviceTopo = pickle.load(file)

    sfcSolver = netcalRandomSolver(substrateTopo,serviceTopo)
    sfcSolver.loadParam()

    netTraceFile = f'netcal_statictopo_{sfcSolver.__class__.__name__}_{sfcNum}.csv'
    TRACER.set(netTraceFile)

    net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver)
    net.start()
    net.stop()

    sfcSolver.saveParam()

    DataAnalysis.getResult(netTraceFile)

