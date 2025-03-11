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

# region 定义基底网络组 ---------------------------------------------------

topoTimeList = [0.0]
topoAdjMatDict = {0.0:np.array([[1,1,0,0],
                                  [1,1,1,0],
                                  [0,1,1,1],
                                  [0,0,1,1]])}
topoWeightMatDict = {0.0:np.array([[0,  10, 0,  0],
                               [10, 0,  10, 0],
                               [0,  10, 0,  10],
                               [0,  0,  10, 0]])}
topoNodeResourceDict = {(0.0,'cpu'):[2,3,4,5],
                    (0.0,'ram'):[3,4,5,6]}
topoLinkResourceDict = {(0.0,'band'):np.array([[1,1,0,0],
                                           [1,1,1,0],
                                           [0,1,1,1],
                                           [0,0,1,1]])}

substrateTopo = SubstrateTopo(topoTimeList,topoAdjMatDict,topoWeightMatDict,topoNodeResourceDict,topoLinkResourceDict)

# endregion

# region 定义服务功能链组 --------------------------------------------------

sfcIdList = [0]                             # sfc 请求的id
sfcLifeTimeDict = {0:[0.1,3.1]}             # sfc 生命周期
endPointDict = {0:[0,3]}                    # sfc 端点部署位置限制（即强制vnf_gnb部署位置）
arriveFunParamDict = {0:[1.0,2.0]}          # sfc 业务参数
vnfRequstDict = {0:[0]}                     # sfc 请求的vnf列表
qosRequesDict = {0:[100]}                   # sfc 请求的qos列表（目前只有时延）

serviceTopo = ServiceTopo(sfcIdList,sfcLifeTimeDict,endPointDict,arriveFunParamDict,vnfRequstDict,qosRequesDict)

# endregion

# region 定义MANO中VNF库 --------------------------------------------------

# MANO中可供部署的vnf库
vnfParamDict = {0:{'unit':3,'factor':0.9,'cpu':1,'ram':1,'type':'vnf_matinv','img':'vnfserver:latest'},
                1:{'unit':2,'factor':1.1,'cpu':1,'ram':1,'type':'vnf_matprint','img':'vnfserver:latest'},
                2:{'unit':1,'factor':1.2,'cpu':1,'ram':1,'type':'vnf_gnb','img':'vnfserver:latest'},
                (0,1):{'band':0.5},
                (1,0):{'band':0.5},
                (0,2):{'band':0.5},
                (2,0):{'band':0.5},
                (1,2):{'band':0.5},
                (2,1):{'band':0.5}}

nfvManager = NfvManager(vnfParamDict)

# endregion

# region 定义SFC部署解决方案 -----------------------------------------------

sfcSolver = FixedSolver(substrateTopo,serviceTopo)

# endregion

# region 定义部署结果追踪器 -------------------------------------------------

netTraceFile = f'multisfc_staticopo_{sfcSolver.__class__.__name__}_{TRACER.get_time_stamp()}.csv'
TRACER.set(netTraceFile)

# endregion

# region 将各组件代入仿真引擎 ------------------------------------------------

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver,useContainter=True)
net.start()
## net.addCLI()
net.stop()

# endregion

# region 分析仿真结果 -------------------------------------------------------

DataAnalysis.getResult(netTraceFile)

# endregion

