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
from custom.netcalSolver import netcalPsoSolver
import numpy as np
np.seterr(over='warn')
import pickle
import code
import random

jsonReader = JsonReader('stk_data_24_06_May_2024_08_00_00.000.json')

topoNodeNames = jsonReader.all_node_list
topoNodeNum_Sat = jsonReader.sat_num
topoNodeNum_Base = jsonReader.base_num
topoNodeNum_Uav = jsonReader.uav_num
topoAdjMat = jsonReader.getAdjacencyMat()
topoWeightMat = jsonReader.getWeightMat()

topoSize = len(topoNodeNames)
topoTimeList = [0.0]
topoAdjMatDict = {topoTime:topoAdjMat for topoTime in topoTimeList}
topoWeightMatDict = {topoTime:topoWeightMat for topoTime in topoTimeList}
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

with open(f"{substrateTopo.__class__.__name__}_{TRACER.get_time_stamp()}.pkl", "wb") as file:
    pickle.dump(substrateTopo, file)


# -------------------------------------------------------------------------------------------------------------------------------------------

for sfcNum in range(300,900,100):
    sfcVnfTypeNum = 10
    sfcIdList = [i for i in range(sfcNum)]
    sfcVnfIdList = [i for i in range(sfcVnfTypeNum)]

    sfcNum_URLLC = int(sfcNum*(2/8))
    sfcNum_mMTC = int(sfcNum*(5/8))
    sfcNum_eMBB = sfcNum-(sfcNum_URLLC+sfcNum_mMTC)

    sfcArriveTime = [1.0] * sfcNum
    sfcLifeTimeDict = {sfcIdList[i]:[sfcArriveTime[i],2.0] for i in range(sfcNum)}
    sfcEndPointDict = {sfcIdList[i]:[random.sample(range(topoSize),1)[0],random.sample(range(topoSize),1)[0]] for i in range(sfcNum)}

    sfcArriveRate_URLLC = NumberGen.getVector(sfcNum_URLLC,**{'distribution':'uniform','dtype':'float','low':0.008000,'high':0.064000})*10 # Consider the number of users
    sfcArriveRate_mMTC = NumberGen.getVector(sfcNum_mMTC,**{'distribution':'uniform','dtype':'float','low':0.100000,'high':0.500000})*10 # Consider the number of users
    sfcArriveRate_eMBB = NumberGen.getVector(sfcNum_eMBB,**{'distribution':'uniform','dtype':'float','low':3.000000,'high':9.500000})*10 # Consider the number of users
    sfcArriveRate = np.concatenate((sfcArriveRate_URLLC,sfcArriveRate_mMTC,sfcArriveRate_eMBB))

    sfcBurstBit_URLLC = NumberGen.getVector(sfcNum_URLLC,**{'distribution':'uniform','dtype':'float','low':0.001600,'high':0.004000})*10 # Consider the number of users
    sfcBurstBit_mMTC = NumberGen.getVector(sfcNum_mMTC,**{'distribution':'uniform','dtype':'float','low':0.004000,'high':0.008000})*10 # Consider the number of users
    sfcBurstBit_eMBB = NumberGen.getVector(sfcNum_eMBB,**{'distribution':'uniform','dtype':'float','low':1.000000,'high':2.000000})*10 # Consider the number of users
    sfcBurstBit = np.concatenate((sfcBurstBit_URLLC,sfcBurstBit_mMTC,sfcBurstBit_eMBB))

    sfcUnitBit_URLLC = NumberGen.getVector(sfcNum_URLLC,**{'distribution':'uniform','dtype':'float','low':0.000160,'high':0.001200})
    sfcUnitBit_mMTC = NumberGen.getVector(sfcNum_mMTC,**{'distribution':'uniform','dtype':'float','low':0.000400,'high':0.004000})
    sfcUnitBit_eMBB = NumberGen.getVector(sfcNum_eMBB,**{'distribution':'uniform','dtype':'float','low':0.000500,'high':0.005000})
    sfcUnitBit = np.concatenate((sfcUnitBit_URLLC,sfcUnitBit_mMTC,sfcUnitBit_eMBB))

    sfcLatencyRequest_URLLC = NumberGen.getVector(sfcNum_URLLC,**{'distribution':'uniform','dtype':'float','low':0.1,'high':0.150})
    sfcLatencyRequest_mMTC = NumberGen.getVector(sfcNum_mMTC,**{'distribution':'uniform','dtype':'float','low':0.1,'high':0.300})
    sfcLatencyRequest_eMBB = NumberGen.getVector(sfcNum_eMBB,**{'distribution':'uniform','dtype':'float','low':0.1,'high':0.400})
    sfcLatencyRequest = np.concatenate((sfcLatencyRequest_URLLC,sfcLatencyRequest_mMTC,sfcLatencyRequest_eMBB))

    sfcParamTemp = [[sfcArriveRate[i],sfcBurstBit[i],sfcUnitBit[i],sfcLatencyRequest[i]] for i in range(sfcNum)]
    random.shuffle(sfcParamTemp)
    sfcParamTemp = np.array(sfcParamTemp)
    sfcArriveRate = sfcParamTemp[:,0]
    sfcBurstBit = sfcParamTemp[:,1]
    sfcUnitBit = sfcParamTemp[:,2]
    sfcLatencyRequest = sfcParamTemp[:,3]

    sfcArriveFunParamDict = {sfcIdList[i]:[sfcArriveRate[i],sfcBurstBit[i],sfcUnitBit[i]] for i in range(sfcNum)}
    sfcVnfNum = NumberGen.getVector(sfcNum,**{'distribution':'uniform','dtype':'int','low':5,'high':10})
    sfcVnfRequstDict = {sfcIdList[i]:random.sample(sfcVnfIdList,sfcVnfNum[i]) for i in range(sfcNum)}
    sfcQosRequestDict = {sfcIdList[i]:[sfcLatencyRequest[i]] for i in range(sfcNum)}

    serviceTopo = ServiceTopo(sfcIdList,sfcLifeTimeDict,sfcEndPointDict,sfcArriveFunParamDict,sfcVnfRequstDict,sfcQosRequestDict)

    with open(f"{serviceTopo.__class__.__name__}_{sfcNum}.pkl", "wb") as file:
        pickle.dump(serviceTopo, file)

# -----------------------------------------------------------------------------------------------------------------------------------------

# In net calculus only param factors are used
vnfDataFactor = NumberGen.getVector(sfcVnfTypeNum,**{'distribution':'uniform','dtype':'float','low':0.8,'high':1.2})
vnfParamDict_node = {sfcVnfIdList[i]:{'factor':vnfDataFactor[i],'cpu':None,'ram':None} for i in range(sfcVnfTypeNum)}
vnfParamDict_link = {(sfcVnfIdList[i],sfcVnfIdList[j]):{'band':None} for i in range(sfcVnfTypeNum) for j in range(sfcVnfTypeNum)}
vnfParamDict = {**vnfParamDict_node,**vnfParamDict_link}

nfvManager = NfvManager(vnfParamDict)

with open(f"{nfvManager.__class__.__name__}_{TRACER.get_time_stamp()}.pkl", "wb") as file:
    pickle.dump(nfvManager, file)
