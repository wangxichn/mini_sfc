
from minisfc.topo import SubstrateTopo,ServiceTopo
from minisfc.mano.vnfm import VnfManager, VnfEm
from minisfc.solver import RadomSolver, GreedySolver
from minisfc.net import Minisfc
from minisfc.trace import TRACER
from util import NumberGen, TopoGen, DataAnalysis
from custom.psoSolver import PsoSolver
from custom.drlSfcpSolver.drlSfcpSolver import DrlSfcpSolver
import numpy as np
import code
import random

topoSize = 30
topoTimeList = [0.0]
topoAdjMatDict = {topoTime:TopoGen.get(topoSize,**{'type':'waxman'}) for topoTime in topoTimeList}
topoWeightMatDict = {topoTime:NumberGen.getMatrix(topoSize,**{'type':'symmetric','dtype':'float','low':0.002,'high':0.02})*topoAdjMatDict[topoTime]
                     for topoTime in topoTimeList}
topoNodeResourceDict_cpu = {(topoTime,'cpu'):NumberGen.getVector(topoSize,**{'distribution':'uniform','dtype':'int','low':20,'high':20})
                            for topoTime in topoTimeList}
topoNodeResourceDict_ram = {(topoTime,'ram'):NumberGen.getVector(topoSize,**{'distribution':'uniform','dtype':'int','low':20,'high':20})
                            for topoTime in topoTimeList}
topoNodeResourceDict = {**topoNodeResourceDict_cpu,**topoNodeResourceDict_ram}
topoLinkResourceDict = {(topoTime,'band'):NumberGen.getMatrix(topoSize,**{'type':'symmetric','dtype':'int','low':200,'high':200})+np.eye(topoSize,dtype=int)*200
                        for topoTime in topoTimeList}

substrateTopo = SubstrateTopo(topoTimeList,topoAdjMatDict,topoWeightMatDict,topoNodeResourceDict,topoLinkResourceDict)

sfcNum = 100
sfcVnfTypeNum = 10
sfcIdList = [i for i in range(sfcNum)]
sfcVnfIdList = [i for i in range(sfcVnfTypeNum)]
sfcArriveTime = [1.0] * sfcNum
sfcLifeTimeDict = {sfcIdList[i]:[sfcArriveTime[i],2.0] for i in range(sfcNum)}
sfcEndPointDict = {sfcIdList[i]:[random.sample(range(topoSize),1)[0],random.sample(range(topoSize),1)[0]] for i in range(sfcNum)}
sfcArriveRate = NumberGen.getVector(sfcNum,**{'distribution':'uniform','dtype':'int','low':8000,'high':64000})
sfcBurstBit = NumberGen.getVector(sfcNum,**{'distribution':'uniform','dtype':'int','low':1600,'high':4000})
sfcUnitBit = NumberGen.getVector(sfcNum,**{'distribution':'uniform','dtype':'int','low':160,'high':1200})
sfcArriveFunParamDict = {sfcIdList[i]:[sfcArriveRate[i],sfcBurstBit[i],sfcUnitBit[i]] for i in range(sfcNum)}
sfcVnfNum = NumberGen.getVector(sfcNum,**{'distribution':'uniform','dtype':'int','low':5,'high':10})
sfcVnfRequstDict = {sfcIdList[i]:random.sample(sfcVnfIdList,sfcVnfNum[i]) for i in range(sfcNum)}
sfcLatencyRequest = NumberGen.getVector(sfcNum,**{'distribution':'uniform','dtype':'float','low':0.1,'high':0.15})
sfcQosRequestDict = {sfcIdList[i]:[sfcLatencyRequest[i]] for i in range(sfcNum)}

serviceTopo = ServiceTopo(sfcIdList,sfcLifeTimeDict,sfcEndPointDict,sfcArriveFunParamDict,sfcVnfRequstDict,sfcQosRequestDict)

vnfDataFactor = NumberGen.getVector(sfcVnfTypeNum,**{'distribution':'uniform','dtype':'float','low':0.8,'high':1.2})
vnfRequstCPU = NumberGen.getVector(sfcVnfTypeNum,**{'distribution':'uniform','dtype':'int','low':1,'high':5})
vnfRequstRAM = NumberGen.getVector(sfcVnfTypeNum,**{'distribution':'uniform','dtype':'int','low':1,'high':5})
vnfRequstBAND = NumberGen.getMatrix(sfcVnfTypeNum,**{'type':'symmetric','dtype':'int','low':10,'high':100})

nfvManager = VnfManager()
for i in range(sfcVnfTypeNum):
    vnfEm_template = VnfEm(**{'vnf_id':i,'vnf_factor':vnfDataFactor[i],'vnf_cpu':vnfRequstCPU[i],'vnf_ram':vnfRequstRAM[i]})
    nfvManager.add_vnf_into_pool(vnfEm_template)

for i in range(sfcVnfTypeNum):
    for j in range(sfcVnfTypeNum):
        nfvManager.add_vnf_service_into_pool(i,j,**{"band":vnfRequstBAND[i][j]})

sfcSolver = DrlSfcpSolver(substrateTopo,serviceTopo,use_cuda=True)
sfcSolver.loadParam()

netTraceFile = f'multisfc_staticopo_{sfcSolver.__class__.__name__}_{TRACER.get_time_stamp()}.csv'
TRACER.set(netTraceFile)

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver)
net.start()
net.stop()

sfcSolver.saveParam()

DataAnalysis.getResult(netTraceFile)

# code.interact(banner="",local=locals())
