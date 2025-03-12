
from minisfc.topo import SubstrateTopo,ServiceTopo
from minisfc.net import Minisfc
from minisfc.trace import TRACER
from minisfc.mano.vnfm import VnfManager, VnfEm

from custom.fixedSolver import FixedSolver
from util import DataAnalysis, RunCommand
import numpy as np
import code

runCommand = RunCommand()
runCommand.clear_container()

code.interact(local=locals())

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
sfcLifeTimeDict = {0:[2,5]}                 # sfc 生命周期
endPointDict = {0:[0,3]}                    # sfc 端点部署位置限制（即强制vnf_gnb部署位置）
arriveFunParamDict = {0:[1.0,2.0]}          # sfc 业务参数
vnfRequstDict = {0:[2,0,2]}                 # sfc 请求的vnf列表
qosRequesDict = {0:[100]}                   # sfc 请求的qos列表（目前只有时延）

serviceTopo = ServiceTopo(sfcIdList,sfcLifeTimeDict,endPointDict,arriveFunParamDict,vnfRequstDict,qosRequesDict)

# endregion

# region 定义MANO中VNF库 --------------------------------------------------

# MANO中可供部署的vnf库
nfvManager = VnfManager()
template_str = "python run_command.py --vnf_name=$vnf_name --vnf_type=$vnf_type --vnf_ip=$vnf_ip --vnf_port=$vnf_port --vnf_cpu=$vnf_cpu --vnf_ram=$vnf_ram --vnf_rom=$vnf_rom"

vnfEm_template = VnfEm(**{'vnf_id':0,'vnf_unit':3,'vnf_factor':0.9,'vnf_cpu':1,'vnf_ram':1,
                          'vnf_type':'vnf_matinv','vnf_img':'vnfserver:latest','vnf_cmd':template_str,'vnf_port':5000})
nfvManager.add_vnf_into_pool(vnfEm_template)
vnfEm_template = VnfEm(**{'vnf_id':1,'vnf_unit':2,'vnf_factor':1.1,'vnf_cpu':1,'vnf_ram':1,
                          'vnf_type':'vnf_matprint','vnf_img':'vnfserver:latest','vnf_cmd':template_str,'vnf_port':5000})
nfvManager.add_vnf_into_pool(vnfEm_template)
vnfEm_template = VnfEm(**{'vnf_id':2,'vnf_unit':1,'vnf_factor':1.2,'vnf_cpu':1,'vnf_ram':1,
                          'vnf_type':'vnf_gnb','vnf_img':'vnfserver:latest','vnf_cmd':template_str,'vnf_port':5000})
nfvManager.add_vnf_into_pool(vnfEm_template)

nfvManager.add_vnf_service_into_pool(0,1,**{"band":0.5})
nfvManager.add_vnf_service_into_pool(1,0,**{"band":0.5})
nfvManager.add_vnf_service_into_pool(0,2,**{"band":0.5})
nfvManager.add_vnf_service_into_pool(2,0,**{"band":0.5})
nfvManager.add_vnf_service_into_pool(1,2,**{"band":0.5})
nfvManager.add_vnf_service_into_pool(2,1,**{"band":0.5})

# endregion

# region 定义SFC部署解决方案 -----------------------------------------------

sfcSolver = FixedSolver(substrateTopo,serviceTopo)

# endregion

# region 定义部署结果追踪器 -------------------------------------------------

netTraceFile = f'multisfc_staticopo_{sfcSolver.__class__.__name__}_{TRACER.get_time_stamp()}.csv'
TRACER.set(netTraceFile)

# endregion

# region 将各组件代入仿真引擎 ------------------------------------------------

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver,use_container=True)

try:
    net.start()
    # net.addCLI()
    net.stop()
    DataAnalysis.getResult(netTraceFile)
except Exception as e:
    runCommand.clear_container()
    TRACER.delete()
    raise e
    
# endregion


