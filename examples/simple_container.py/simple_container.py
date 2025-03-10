import sys
#添加上级目录
sys.path.append("..//..//")
from minisfc.topo import SubstrateTopo,ServiceTopo
from minisfc.mano import NfvManager
from minisfc.net import Minisfc
from minisfc.trace import TRACER
from custom.fixedSolver import FixedSolver
from util import DataAnalysis
import numpy as np
import code

timeList = [0.0]
adjacencyMatDict = {0.0:np.array([[1,1,0,0],
                                  [1,1,1,0],
                                  [0,1,1,1],
                                  [0,0,1,1]])}
weightMatDict = {0.0:np.array([[0,  10, 0,  0],
                               [10, 0,  10, 0],
                               [0,  10, 0,  10],
                               [0,  0,  10, 0]])}
nodeResourceDict = {(0.0,'cpu'):[2,3,4,5],
                    (0.0,'ram'):[3,4,5,6]}
linkResourceDict = {(0.0,'band'):np.array([[1,1,0,0],
                                           [1,1,1,0],
                                           [0,1,1,1],
                                           [0,0,1,1]])}

substrateTopo = SubstrateTopo(timeList,adjacencyMatDict,weightMatDict,nodeResourceDict,linkResourceDict)


sfcIdList = [0]
sfcLifeTimeDict = {0:[0.1,5.1]}
endPointDict = {0:[0,3]}
arriveFunParamDict = {0:[1.0,2.0]}
vnfRequstDict = {0:[0,1,2]}
qosRequesDict = {0:[100]}

serviceTopo = ServiceTopo(sfcIdList,sfcLifeTimeDict,endPointDict,arriveFunParamDict,vnfRequstDict,qosRequesDict)

vnfParamDict = {0:{'unit':3,'factor':0.9,'cpu':1,'ram':1},
                1:{'unit':2,'factor':1.1,'cpu':1,'ram':1},
                2:{'unit':1,'factor':1.2,'cpu':1,'ram':1},
                (0,1):{'band':0.5},
                (1,0):{'band':0.5},
                (0,2):{'band':0.5},
                (2,0):{'band':0.5},
                (1,2):{'band':0.5},
                (2,1):{'band':0.5}}

nfvManager = NfvManager(vnfParamDict)

sfcSolver = FixedSolver(substrateTopo,serviceTopo)

netTraceFile = f'multisfc_staticopo_{sfcSolver.__class__.__name__}_{TRACER.get_time_stamp()}.csv'
TRACER.set(netTraceFile)

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver,useContainter=True)
net.start()
net.stop()

DataAnalysis.getResult(netTraceFile)

