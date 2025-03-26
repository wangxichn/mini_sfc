[中文](./simple_dynamictopo_zh.md) | [English](./simple_dynamictopo_en.md)

# 动态拓扑的数值仿真

使用MiniSFC进行仿真的基本流程同NS3、Mininet等其他网络仿真工具类似，即首先编写一个`.py`的控制脚本文件设定仿真的场景，然后使用`Python`运行该脚本文件，即可启动仿真。

该示例的讲解以项目中`example/simple_dynamictopo.py`为例，介绍使用MiniSFC进行仿真时仿真脚本必要的元素，以及如何对产生的结果进行分析，完成动态拓扑的数值仿真。

## 基本工作流

编写脚本使用MiniSFC进行动态拓扑的数值仿真的流程如图1所示：

![basic_workflow](https://raw.githubusercontent.com/wangxichn/image_hosting/refs/heads/main/minisfc/minisfc_docs-basic_workflow.drawio.png)

<center>图1 使用MiniSFC进行动态拓扑的数值仿真的基本工作流</center>

这个工作流符合构建网络仿真的直觉，即首先构建网络拓扑，然后设置一个预期该网络中需要部署的服务，然后在仿真环境中模拟网络的行为。直到定义MiniSFC仿真器并开始仿真，前面的工作都可以视为准备工作。

## 准备工作

为了对每次仿真结果进行标记，MiniSFC提供了一个`Trace`类，该类可以记录仿真过程中产生的信息，并提供时间戳进行标记。

```python
from minisfc.trace import Trace

SIMULATION_ID = Trace.get_time_stamp()
```

### 步骤一：定义基底网络拓扑

首先，需要构建一个基底网络拓扑，即一个包含所有节点和链路的网络拓扑。这个拓扑可以是静态的，也可以是动态的。不论是静态的还是动态的，都需要包含以下几个元素才可完整定义基底网络所需的信息。

- 时间：一个时间序列，用于标记网络拓扑发生变化的时间点，该时间默认以秒为单位，支持浮点数精度。如果需要构建的是静态的网络拓扑，则时间序列只包含一个元素，即基底网络的建立时间0.0。如果需要构建的是动态的网络拓扑，则时间序列包含多个元素，即网络拓扑发生变化的时间点。MiniSFC会根据该信息来自动生成事件，标记网络拓扑此时发生的了变化，并对网络进行相应的调整。

```python
topoTimeList = [0.0,12.0,20.0]
```

- 邻接矩阵字典：一个以时间为索引的邻接矩阵字典，用于描述网络运行过程中不同时间点的节点之间的连接关系。矩阵的行数和列数分别为节点的数量，矩阵中的元素表示节点i和节点j之间是否存在一条链路。该字典的键需要与时间序列中的元素严格一一对应。需要注意的是该邻接矩阵需包含自环，这么做是基于部署在同一个物理设置上的不同VNF可以通过内部链路进行通信。

```python
topoAdjMatDict = {0.0:np.array([[1,1,1],
                                  [1,1,1],
                                  [1,1,1]]),
                    12.0:np.array([[1,0,1],
                                  [0,1,1],
                                  [1,1,1]]),
                    20.0:np.array([[1,1,1],
                                  [1,1,0],
                                  [1,0,1]])}
```

- 链路权重矩阵字典：一个以时间为索引的链路权重矩阵字典，用于描述网络运行过程中不同时间点的链路的权重。矩阵的行数和列数分别为节点的数量，矩阵中的元素表示节点i和节点j之间的链路的权重。该字典的键需要与时间序列中的元素严格一一对应。该权值默认为两个节点之间的传播延迟，单位为毫秒。需要注意各个权值矩阵应与邻接矩阵中的元素一一对应。即基于这样一种假设，两个节点之间不存在链路是，其权值矩阵中的元素应该为0或无穷大（因为节点的可达性是基于邻接矩阵的，因此不影响服务的时延累计的计算）。

```python
topoWeightMatDict = {0.0:np.array([[0,20,10], # delay ms
                               [20,0,10],
                               [10,10,0]]),
                 12.0:np.array([[0,0,20],
                               [0,0,10],
                               [20,10,0]]),
                 20.0:np.array([[0,30,10],
                               [30,0,0],
                               [10,0,0]])}
```

- 节点资源字典：一个以时间为索引的节点资源字典，用于描述网络运行过程中不同时间点的节点的资源信息。字典的键为元组，包含时间和资源类型两个元素，值为一个列表，包含每个节点的资源信息。资源类型可以是CPU、内存等，具体取决于想要模拟的网络的资源类型。需要注意的是，资源信息的数量应该与节点的数量相匹配，即每个节点都应该有对应的资源信息。且时间信息应该与时间序列中的元素严格一一对应。

```python
topoNodeResourceDict = {(0.0,'cpu'):[2,4,2], # cores
                    (0.0,'ram'):[256,512,256], # Memmory MB
                    (12.0,'cpu'):[2,4,2],
                    (12.0,'ram'):[256,512,256],
                    (20.0,'cpu'):[2,4,2],
                    (20.0,'ram'):[256,512,256],}
```

- 链路资源字典：一个以时间为索引的链路资源字典，用于描述网络运行过程中不同时间点的链路的资源信息。字典的键为元组，包含时间和资源类型两个元素，值为一个矩阵，包含每个链路的资源信息。资源类型可以是带宽等，具体取决于想要模拟的网络的资源类型。需要注意的是，资源信息的数量应该与链路的数量相匹配，即每个链路都应该有对应的资源信息。且时间信息应该与时间序列中的元素严格一一对应。

```python
topoLinkResourceDict = {(0.0,'band'):np.array([[100,100,100], # bw Mbps
                                           [100,100,100],
                                           [100,100,100]]),
                    (12.0,'band'):np.array([[100,0,100],
                                           [0,100,100],
                                           [100,100,100]]),
                    (20.0,'band'):np.array([[100,100,100],
                                           [100,100,0],
                                           [100,0,100]])}
```

当这些信息准备好后，就可以构建一个来自于Minisfc的`SubstrateTopo`对象，该对象包含了所有网络拓扑信息。

```python
from minisfc.topo import SubstrateTopo

substrateTopo = SubstrateTopo(topoTimeList,topoAdjMatDict,topoWeightMatDict,
                              topoNodeResourceDict,topoLinkResourceDict)
```

为了方便后续的仿真，可以将该`SubstrateTopo`对象保存为一个pickle文件进行固化，即无需每次都重新构建该对象，该方法适用于构建随机网络拓扑的场景并测试不同算法的性能时，进行变量控制。

```python
with open(f"{substrateTopo.__class__.__name__}_{SIMULATION_ID}.pkl", "wb") as file:
    pickle.dump(substrateTopo, file)
```

### 步骤二：定义VNF管理器

SFC所建立的服务是由多个VNF组成的，每个VNF都代表一个具体的功能，这些VNF需要部署在基底网络上，并按照一定顺序部署。MiniSFC提供了`VnfManager`类来管理VNF的部署和调度。因此在仿真之前，需要向`VnfManager`中添加VNF的模板，并设置每个VNF的资源占用信息。该过程类似于用户的服务注册环节，即用户需要向系统中事先注册自己所需的服务，进而在后续运行中，系统根据用户的需求提供相应的服务。

- 实例化：`VnfManager`对象可以直接实例化，不需要任何参数。

```python
from minisfc.mano.vnfm import VnfManager,VnfEm

nfvManager = VnfManager()
```

- 添加VNF模板：VNF在MiniSFC中被抽象为`VnfEm`类，该类包含了VNF的ID、CPU占用、内存占用、带宽占用等信息。`VnfManager`对象提供了`add_vnf_into_pool`方法，用于向其内部的VNF模板池中添加VNF模板。需要注意的是，VNF模板的ID必须是唯一的，且不能与其他VNF模板的ID重复。'vnf_cpu'的值应该是浮点数，表示VNF的CPU占用，单位为核数。'vnf_ram'的值应该是整数，表示VNF的内存占用，单位为MB。

```python
vnfEm_template = VnfEm(**{'vnf_id':0,'vnf_cpu':0.2,'vnf_ram':64})
nfvManager.add_vnf_into_pool(vnfEm_template)
vnfEm_template = VnfEm(**{'vnf_id':1,'vnf_cpu':0.15,'vnf_ram':64})
nfvManager.add_vnf_into_pool(vnfEm_template)
vnfEm_template = VnfEm(**{'vnf_id':2,'vnf_cpu':0.15,'vnf_ram':64})
nfvManager.add_vnf_into_pool(vnfEm_template)
```

- 设置VNF间虚拟链路资源占用：`VnfManager`对象提供了`set_vnf_resource_info`方法，用于设置VNF间的虚拟链路资源占用信息。该方法需要三个参数，前两个参数为VNF的ID，第三个参数为资源占用信息。资源占用信息是一个字典，包含资源类型和占用量两个元素，资源类型默认支持单位为MB的带宽，具体取决于想要模拟的网络的资源类型。

```python
nfvManager.add_vnf_service_into_pool(0,1,**{"band":20})
nfvManager.add_vnf_service_into_pool(1,2,**{"band":20})
nfvManager.add_vnf_service_into_pool(2,1,**{"band":20})
```

- 保存VNF管理器：为了方便后续的仿真，可以将`VnfManager`对象保存为一个pickle文件进行固化，即无需每次都重新构建该对象，该方法适用于构建随机网络拓扑的场景并测试不同算法的性能时，进行变量控制。

```python
with open(f"{nfvManager.__class__.__name__}_{SIMULATION_ID}.pkl", "wb") as file:
    pickle.dump(nfvManager, file)
```

### 步骤三：定义SFC拓扑

SFC拓扑是指部署在基底网络上的服务流，它由多个服务节点和服务链路组成。每个服务节点都代表一个具体的服务，该示例中我们进行的是基于数值的仿真，因此该服务为虚拟的，仅仅体现在对基底网络中物理节点设置的资源占用。

- ID：一个整数列表，用于标记SFC的ID。该值将用来标记每个SFC的唯一性，且该列表的长度应该与服务链路的数量相匹配。在仿真结束后生成的日志记录中，会包含每个SFC的ID，方便后续的分析。需要注意的是，SFC的ID不能重复，否则会导致仿真结果的错误。

```python
sfcIdList = [0,1,2]
```

- 生命周期：一个以SFC ID为索引的字典，用于描述SFC的生命周期。字典的键为SFC的ID，值为一个列表，包含两个元素，分别为SFC的建立时间和终止时间。该值以秒为单位，且生命周期的终止时间应该大于等于建立时间。MiniSFC会根据该信息来自动生成事件，调度每一个SFC的部署和终止，并在最后一个生命周期终止时停止仿真。需要注意的是，该字典的键需要与SFC ID列表中的元素严格一一对应。

```python
sfcLifeTimeDict = {0:[5,25],
                   1:[10,30],
                   2:[15,35]}
```

- 端点：一个以SFC ID为索引的字典，用于描述SFC的端点。端点的设置基于这样一种假设，即用户对其请求服务的接入接出点是基于用户与网络设施的相对物理位置的，当由于网络拓扑的变化而导致服务的接入接出点发生变化时，用户应当重新请求服务（此处是当前版本V2.0的权宜之计，后续版本将设计更符合实际情况的动态设置方法）。字典的键为SFC的ID，值为一个列表，包含SFC的接入接出点对应的基底网络上的物理节点ID。要注意的是，该字典的键需要与SFC ID列表中的元素严格一一对应。

```python
endPointDict = {0:[0,1],
                1:[0,2],
                2:[1,2]}
```

- VNF请求：一个以SFC ID为索引的字典，用于描述SFC的VNF请求。字典的键为SFC的ID，值为一个列表，包含SFC所需的VNF的ID，其中的ID值即为VNF模板池中VNF模板的ID，列表的长度即为SFC所需的VNF数量，由于不同VNF的功能不同，因此该列表中允许出现相同的VNF ID，即使用一个VNF模版分别创建不同的实例进行部署。需要注意的是，该字典的键需要与SFC ID列表中的元素严格一一对应。

```python
vnfRequstDict = {0:[0,1,2],
                 1:[0,1],
                 2:[2,1]}
```

- 服务QoS需求：一个以SFC ID为索引的字典，用于描述SFC的QoS需求。字典的键为SFC的ID，值为一个列表，包含SFC的QoS需求，这里与基底网络中节点之间的传输时延对应，单位为毫秒，该值表示SFC的端到端时延要求。需要注意的是，该字典的键需要与SFC ID列表中的元素严格一一对应。

```python
qosRequesDict = {0:[100],
                 1:[100],
                 2:[100]}
```

在这些信息准备好后，就可以构建一个来自于Minisfc的`ServiceTopo`对象，该对象包含了所有SFC拓扑信息。

```python
from minisfc.topo import ServiceTopo
serviceTopo = ServiceTopo(sfcIdList,sfcLifeTimeDict,endPointDict,vnfRequstDict,qosRequesDict)
```

为了方便后续的仿真，可以将该`ServiceTopo`对象保存为一个pickle文件进行固化，即无需每次都重新构建该对象，该方法适用于构建随机网络拓扑的场景并测试不同算法的性能时，进行变量控制。

```python
with open(f"{serviceTopo.__class__.__name__}_{SIMULATION_ID}.pkl", "wb") as file:
    pickle.dump(serviceTopo, file)
```

### 步骤四：定义SFC部署求解器

MiniSFC提供了多种SFC部署求解器，用于求解SFC在基底网络上的部署方案。在仿真之前，需要选择一个部署求解器，该求解器可以来自于Minisfc的`SfcSolver`类例如`RandomSolver`、`GreedySolver`等，也可以来自于用户集成了Minisfc的`SfcSolver`类后实现的自定义求解器，例如`PsoSolver`。

`SfcSolver`对象的实例化需要两个参数，第一个参数为`SubstrateTopo`对象，第二个参数为`ServiceTopo`对象，这两个对象分别代表了基底网络拓扑和SFC拓扑，可用于求解器的初始化。因此我们默认求解器具备未来网络发生事件的全部信息，因此可用于基于学习类的预测算法。当然如果用户希望实现一个完全基于突发事件的求解器，则可以忽略掉这两个参数，而是仅根据事件发生时的信息进行计算。

```python
from minisfc.solver import RandomSolver, GreedySolver
from custom.psoSolver import PsoSolver

sfcSolver = RadomSolver(substrateTopo,serviceTopo)
```

### 步骤五：定义MiniSFC仿真器

MiniSFC提供了`Minisfc`类来进行仿真，该类包含了仿真的主要逻辑，包括事件驱动、事件处理、事件调度、仿真结果记录等。

`Minisfc`对象的实例化需要四个参数，第一个参数为`SubstrateTopo`对象，第二个参数为`ServiceTopo`对象，第三个参数为`VnfManager`对象，第四个参数为`SfcSolver`对象，即为前面定义的准备好的对象。

```python
from minisfc.net import Minisfc

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver)
```

## 开始仿真

在仿真开始之前，允许用户自定义仿真结果的保存路径或文件名，默认路径为运行脚本所在的当前目录。

MiniSFC默认提供了两种仿真结果记录方式，一种是基于事件的记录，即记录每一个事件的发生时间、事件类型、事件相关的对象、事件相关的属性等信息，该方式可以用于算法性能以及执行结果的分析。另一种是基于每个物理节点的记录，即记录每一个事件发生时间时，每个物理节点的CPU、内存占用情况，该方式可以用于对比不同算法对资源的分配情况。用户可以根据自己的需求设计新的仿真结果记录条目，只需继承`TraceResult`或`TraceNfvi`类，并参照其在MANO中的调用方式，重写所需方法即可。

```python
TraceResultFile = f'{TRACE_RESULT.__class__.__name__}_{sfcSolver.__class__.__name__}_{SIMULATION_ID}.csv'
TRACE_RESULT.set(TraceResultFile)
TraceNfviFile = f'{TRACE_NFVI.__class__.__name__}_{sfcSolver.__class__.__name__}_{SIMULATION_ID}.csv'
TRACE_NFVI.set(TraceNfviFile)
```

上述工作完成后，就可以启动仿真，该过程会自动生成事件并进行调度，直到所有SFC的生命周期终止。`net.stop()`在基于数值的仿真中不重要，因为在所有的事件都处理完后，仿真会自动停止。因此可以不用调用该方法。（为了体现仿真的完整性和规范性，这里还是调用了该方法）但是在基于容器的模拟仿真中，该方法是必须的，因为需要该方法释放仿真过程中所占用的资源并退出Containernet仿真环境，避免对下次仿真造成影响。

```python
net.start()
net.stop()
```

如果使用示例中的默认脚本，则运行如下命令：

```bash
cd minisfc/examples/simple_dynamictopo
python simple_dynamictopo.py
```

如果使用了Anaconda环境（例如命名为`minisfc`的开发环境），则运行如下命令：

```bash
cd minisfc/examples/simple_dynamictopo
conda activate minisfc
python simple_dynamictopo.py
```

## 仿真过程

在仿真运行过程中，会在执行该脚本中的终端创建一个基于`tqdm`的进度条，显示仿真的进度。该进度条会显示当前仿真时间、当前仿真事件等信息。可用于观察仿真的运行情况，以及当仿真突然中断时，可以根据进度条信息来进行调试。

## 结果分析

当仿真结束后，脚本所在的工作目录下会生成两个日志记录文件：

- `TraceResult_{SolverName}_{SimulationID}.csv`：该日志文件的记录条目为`Event,Time,SfcId,Result,Resource,Vnffgs,Solution,Reason`
    - `Event`：事件类型，参考NS3的设置，这里使用了`+`来表示SFC请求的到来，`-`来表示SFC生命周期终止，`t`来表示基底网络拓扑发生变化。
    - `Time`：事件发生的时间，单位为秒。
    - `SfcId`：事件相关的SFC的ID。
    - `Result`：事件的结果，`True`表示SFC部署成功，`False`表示SFC部署失败。
    - `Resource`：事件发生时全网的剩余资源情况，格式为`[cpu:mem:band]`，分别表示CPU、内存、带宽的剩余资源。
    - `Vnffgs`：事件发生时在网运行的SFC情况，格式为`[SFC_ID]`。
    - `Solution`：事件的部署方案，格式为`vnffg1:node1,vnffg2:node2,vnffg3:node3`，即该事件部署的SFC上的每个VNF部署在哪个基底网络节点上。
    - `Reason`：事件的原因，当事件类型为`-`或`t`时，该字段记录了SFC的终止原因（例如超时、资源不足等）。

- `TraceNfvi_{SolverName}_{SimulationID}.csv`：该日志文件的记录条目为`Event,Time,NVFI_0_cpu,NVFI_0_ram,NVFI_0_vnfs,NVFI_1_cpu...`
    - `Event`：事件类型，参考NS3的设置，这里使用了`+`来表示SFC请求的到来，`-`来表示SFC生命周期终止，`t`来表示基底网络拓扑发生变化。
    - `Time`：事件发生的时间，单位为秒。
    - `NVFI_i_cpu`：第i个节点的CPU占用情况，单位为核数。
    - `NVFI_i_ram`：第i个节点的内存占用情况，单位为MB。
    - `NVFI_i_vnfs`：第i个节点上运行的VNF的ID列表。

用户可以根据自己的需求对日志文件进行分析，例如绘制仿真结果图表、分析SFC部署失败的原因、分析资源的分配情况等。

在`examples/simple_dynamictopo`目录下提供了一个基于`matplotlib`的仿真结果分析示例，参考文件`draw_nvfi_statues.py`，绘制了网络运行过程中每个节点的CPU、内存占用情况,如下图所示：

![nvfi_status](https://raw.githubusercontent.com/wangxichn/image_hosting/8d050cee9eb6301e3ce60a4f81a923b01bf5cd60/minisfc/draw_simple_dynamictopo_nvfi_statues.svg)
