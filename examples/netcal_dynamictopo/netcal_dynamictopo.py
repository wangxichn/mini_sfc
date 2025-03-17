
from minisfc.topo import SubstrateTopo,ServiceTopo
from minisfc.mano.vnfm import VnfManager, VnfEm
from minisfc.net import Minisfc
from minisfc.trace import TRACER
from minisfc.util import NumberGen, DataAnalysis, JsonReader
from custom.netcalSolver import netcalPsoSolver, netcalRandomSolver
import numpy as np
np.seterr(over='warn')
import pickle
import code
import random
import os

jsondir = 'SSG-Json-RawData'
jsonfiles = [os.path.join(jsondir, file) for file in os.listdir(jsondir)]

jsonReader = JsonReader(jsonfiles[0])
topoNodeNames = jsonReader.all_node_list
topoNodeNum_Sat = jsonReader.sat_num
topoNodeNum_Base = jsonReader.base_num
topoNodeNum_Uav = jsonReader.uav_num
# topoAdjMat = jsonReader.getAdjacencyMat()
# topoWeightMat = jsonReader.getWeightMat()

topoSize = len(topoNodeNames)
topoTimeList = list(np.arange(0.0,600.0,10.0))
topoAdjMatDict = {topoTime:JsonReader(jsonfiles[i]).getAdjacencyMat() for i,topoTime in enumerate(topoTimeList)}
topoWeightMatDict = {topoTime:JsonReader(jsonfiles[i]).getWeightMat() for i,topoTime in enumerate(topoTimeList)}
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

sfcNum = 300
sfcVnfTypeNum = 10
sfcIdList = [i for i in range(sfcNum)]
sfcVnfIdList = [i for i in range(sfcVnfTypeNum)]

sfcNum_URLLC = int(sfcNum*(2/8))
sfcNum_mMTC = int(sfcNum*(5/8))
sfcNum_eMBB = sfcNum-(sfcNum_URLLC+sfcNum_mMTC)

sfcArriveTime = np.cumsum(NumberGen.getVector(sfcNum,**{'distribution':'possion','dtype':'float','lam':0.55,'reciprocal':True}))
sfcLifeLength = NumberGen.getVector(sfcNum,**{'distribution':'uniform','dtype':'float','low':5,'high':60})
sfcLifeTimeDict = {sfcIdList[i]:[sfcArriveTime[i],sfcArriveTime[i]+sfcLifeLength[i]] for i in range(sfcNum)}
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

# In net calculus only param factor is used
vnfDataFactor = NumberGen.getVector(sfcVnfTypeNum,**{'distribution':'uniform','dtype':'float','low':0.8,'high':1.2})
nfvManager = VnfManager()
for i in range(sfcVnfTypeNum):
    vnfEm_template = VnfEm(**{'vnf_id':i,'vnf_factor':vnfDataFactor[i]})
    nfvManager.add_vnf_into_pool(vnfEm_template)
for i in range(sfcVnfTypeNum):
    for j in range(sfcVnfTypeNum):
        nfvManager.add_vnf_service_into_pool(i,j,**{"band":None})


with open(f"{substrateTopo.__class__.__name__}_{TRACER.get_time_stamp()}.pkl", "wb") as file:
    pickle.dump(substrateTopo, file)
with open(f"{serviceTopo.__class__.__name__}_{TRACER.get_time_stamp()}.pkl", "wb") as file:
    pickle.dump(serviceTopo, file)
with open(f"{nfvManager.__class__.__name__}_{TRACER.get_time_stamp()}.pkl", "wb") as file:
    pickle.dump(nfvManager, file)

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
