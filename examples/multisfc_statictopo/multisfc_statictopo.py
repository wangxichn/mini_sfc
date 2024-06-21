import sys
#添加上级目录
sys.path.append("..//..//")
from minisfc.topo import SubstrateTopo,ServiceTopo
from minisfc.mano import NfvManager
from minisfc.solver import RadomSolver, GreedySolver
from minisfc.net import Minisfc
from minisfc.trace import TRACER
from util import NumberGen, TopoGen, DataAnalysis
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
sfcArriveTime = np.cumsum(NumberGen.getVector(sfcNum,**{'distribution':'possion','dtype':'float','lam':1.2,'reciprocal':True}))
sfcLifeLength = NumberGen.getVector(sfcNum,**{'distribution':'uniform','dtype':'float','low':5,'high':10})
sfcLifeTimeDict = {sfcIdList[i]:[sfcArriveTime[i],sfcArriveTime[i]+sfcLifeLength[i]] for i in range(sfcNum)}
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
vnfRequstCPU = NumberGen.getVector(sfcVnfTypeNum,**{'distribution':'uniform','dtype':'int','low':1,'high':10})
vnfRequstRAM = NumberGen.getVector(sfcVnfTypeNum,**{'distribution':'uniform','dtype':'int','low':1,'high':10})
vnfRequstBAND = NumberGen.getMatrix(sfcVnfTypeNum,**{'type':'symmetric','dtype':'int','low':10,'high':100})
vnfParamDict_node = {sfcVnfIdList[i]:{'factor':vnfDataFactor[i],'cpu':vnfRequstCPU[i],'ram':vnfRequstRAM[i]} 
                     for i in range(sfcVnfTypeNum)}
vnfParamDict_link = {(sfcVnfIdList[i],sfcVnfIdList[j]):{'band':vnfRequstBAND[i,j]} 
                     for i in range(sfcVnfTypeNum) for j in range(sfcVnfTypeNum)}
vnfParamDict = {**vnfParamDict_node,**vnfParamDict_link}

nfvManager = NfvManager(vnfParamDict)

sfcSolver = RadomSolver(substrateTopo,serviceTopo)

netTraceFile = f'multisfc_staticopo_{sfcSolver.__class__.__name__}_{TRACER.get_time_stamp()}.csv'
TRACER.set(netTraceFile)

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver)
net.start()
net.stop()

DataAnalysis.getResult(netTraceFile)

# code.interact(banner="",local=locals())
