
from minisfc.topo import SubstrateTopo,ServiceTopo
from minisfc.mano.vnfm import VnfManager,VnfEm
from minisfc.solver import RadomSolver
from minisfc.net import Minisfc
from minisfc.trace import TRACER
import numpy as np
import code

timeList = [0.0,0.2,0.3]
adjacencyMatDict = {0.0:np.array([[1,1,1],
                                  [1,1,1],
                                  [1,1,1]]),
                    0.2:np.array([[1,0,1],
                                  [0,1,1],
                                  [1,1,1]]),
                    0.3:np.array([[1,1,1],
                                  [1,1,0],
                                  [1,0,1]])}
weightMatDict = {0.0:np.array([[0,2,1],
                               [2,0,1],
                               [1,1,0]]),
                 0.2:np.array([[0,0,2],
                               [0,0,1],
                               [2,1,0]]),
                 0.3:np.array([[0,3,1],
                               [3,0,0],
                               [1,0,0]])}
nodeResourceDict = {(0.0,'cpu'):[2,3,4],
                    (0.0,'ram'):[3,4,5],
                    (0.2,'cpu'):[2,3,4],
                    (0.2,'ram'):[3,4,5],
                    (0.3,'cpu'):[2,3,4],
                    (0.3,'ram'):[3,4,5],}
linkResourceDict = {(0.0,'band'):np.array([[9,8,7],
                                           [8,9,8],
                                           [7,8,9]]),
                    (0.2,'band'):np.array([[9,0,7],
                                           [0,9,8],
                                           [7,8,9]]),
                    (0.3,'band'):np.array([[9,8,7],
                                           [8,9,0],
                                           [7,0,9]])}

substrateTopo = SubstrateTopo(timeList,adjacencyMatDict,weightMatDict,nodeResourceDict,linkResourceDict)


sfcIdList = [1,3,10]
sfcLifeTimeDict = {1:[0.11,0.15],
                   3:[0.12,0.22],
                   10:[0.21,0.32]}
endPointDict = {1:[0,1],
                3:[0,2],
                10:[1,2]}
arriveFunParamDict = {1:[1.0,2.0],
                      3:[1.1,2.1],
                      10:[1.2,2.2]}
vnfRequstDict = {1:[0,1,2],
                 3:[0,1],
                 10:[2,1]}
qosRequesDict = {1:[100],
                 3:[100],
                 10:[100]}

serviceTopo = ServiceTopo(sfcIdList,sfcLifeTimeDict,endPointDict,arriveFunParamDict,vnfRequstDict,qosRequesDict)


nfvManager = VnfManager()
vnfEm_template = VnfEm(**{'vnf_id':0,'vnf_factor':0.9,'vnf_cpu':1,'vnf_ram':1})
nfvManager.add_vnf_into_pool(vnfEm_template)
vnfEm_template = VnfEm(**{'vnf_id':1,'vnf_factor':1.1,'vnf_cpu':1,'vnf_ram':1})
nfvManager.add_vnf_into_pool(vnfEm_template)
vnfEm_template = VnfEm(**{'vnf_id':2,'vnf_factor':1.2,'vnf_cpu':1,'vnf_ram':1})
nfvManager.add_vnf_into_pool(vnfEm_template)

nfvManager.add_vnf_service_into_pool(0,1,**{"band":0.5})
nfvManager.add_vnf_service_into_pool(1,0,**{"band":0.5})
nfvManager.add_vnf_service_into_pool(0,2,**{"band":0.5})
nfvManager.add_vnf_service_into_pool(2,0,**{"band":0.5})
nfvManager.add_vnf_service_into_pool(1,2,**{"band":0.5})
nfvManager.add_vnf_service_into_pool(2,1,**{"band":0.5})

sfcSolver = RadomSolver(substrateTopo,serviceTopo)

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver)
net.start()
net.stop()

