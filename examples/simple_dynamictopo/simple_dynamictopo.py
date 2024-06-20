import sys
#添加上级目录
sys.path.append("..//..//")
from minisfc.topo import SubstrateTopo,ServiceTopo
from minisfc.mano import NfvManager
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
qosRequesDict = {1:[5],
                 3:[6],
                 10:[4]}

serviceTopo = ServiceTopo(sfcIdList,sfcLifeTimeDict,endPointDict,arriveFunParamDict,vnfRequstDict,qosRequesDict)

vnfParamDict = {0:{'unit':3,'factor':0.9,'cpu':0,'ram':0},
                1:{'unit':2,'factor':1.1,'cpu':0,'ram':0},
                2:{'unit':1,'factor':1.2,'cpu':0,'ram':0},
                (0,1):{'band':25},
                (1,0):{'band':25},
                (0,2):{'band':25},
                (2,0):{'band':25},
                (1,2):{'band':25},
                (2,1):{'band':25}}

nfvManager = NfvManager(vnfParamDict)

sfcSolver = RadomSolver(substrateTopo,serviceTopo)

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver)
net.start()
net.stop()

