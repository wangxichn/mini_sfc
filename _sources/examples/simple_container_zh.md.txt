[中文](./simple_container_zh.md) | [English](./simple_container_en.md)

# 基于容器的模拟仿真环境的简单示例

使用MiniSFC进行仿真的基本流程同NS3、Mininet等其他网络仿真工具类似，即首先编写一个`.py`的控制脚本文件设定仿真的场景，然后使用`Python`运行该脚本文件，即可启动仿真。

该示例的讲解以项目中`example/simple_container.py`为例，介绍使用MiniSFC进行仿真时仿真脚本必要的元素，以及如何对产生的结果进行分析，完成基于容器的模拟仿真环境的简单示例。

## 基本工作流

编写脚本使用MiniSFC进行基于容器的模拟仿真环境的简单示例的流程如图1所示：

![container_workflow](https://raw.githubusercontent.com/wangxichn/image_hosting/refs/heads/main/minisfc/minisfc_docs-container_workflow.drawio.png)

<center>图1 使用MiniSFC进行基于容器的模拟仿真环境的简单示例的基本工作流</center>

这个工作流符合构建网络仿真的直觉，即首先构建网络拓扑，然后设置一个预期该网络中需要部署的服务，然后在仿真环境中模拟网络的行为。直到定义MiniSFC仿真器并开始仿真，前面的工作都可以视为准备工作。

## 关于容器

<mark>需要注意的是，相比基于简单的数值仿真，基于容器的模拟仿真要求实际地在网络中部署容器，以及在容器中运行着相应的服务来支持仿真。因此在运行仿真之前，需要预先准备好预期在网络中部署的容器镜像，以及相应的服务启动和使用方式。</mark>

在该示例中我们提供了分别用于构建vnf和ue的两个docker镜像：
- vnf镜像制作文件：`Dockerfile.vnfserver`
    - 其上部署一个支持三种类型vnf功能的基于FastAPI开发的Web服务器
    - 该服务器的原文件位于`example/simple_container/mini_vnf`
    - 三种类型的vnf功能分别为：
        - 功能1：`vnf_gnb`用于简单模拟移动通信中的基站的接入功能，本质上是将用户的请求转发到指定的下一个vnf节点。
        - 功能2：`vnf_matinv`用于将用户请求的数据矩阵多次进行求逆运算（模拟高计算负载任务），并将运算结果转发到指定的下一个vnf节点。
        - 功能3：`vnf_matprint`用于将用户请求的数据矩阵打印出来。
    - vnf的具体功能是通过服务器启动指令中的`vnf_type`参数来指定的
    - 不管那种类型的vnf其内容都在维护一个转发表，即来自于哪个用户的请求对应着应该将处理结果转发到哪个vnf节点。
    - 因此服务器对外提供一个设置转发表的Restful接口，用户可以通过该接口设置转发表，以便控制vnf的功能(已被Minisfc中的MANO根据SFC的部署情况自动实现)。
    - 正常启动各个服务的容器，并完成相应的转发表设置后，用户即可向vnf链的首个vnf节点发送请求，链上的转发和计算功能将自动完成，并将结果返回给目标用户。
    - 用户可以参考该镜像的功能，编写自己的vnf镜像，并将其部署在MiniSFC仿真器中（建议在`mini_vnf`的基础上进行扩展减少意外错误，每次修改完代码后都需要重新构建镜像）。
    - 详细的vnf镜像制作过程将在后续的步骤中介绍。
- ue镜像制作文件：`Dockerfile.ueserver`
    - 为了便于MiniSFC作为整个仿真场景的总指挥，对网络中的各个实体进行统一的管理和控制，我们将用户模型也通过容器进行封装和部署
    - 其上部署一个支持两种类型ue功能的基于FastAPI开发的Web服务器
    - 该服务器的原文件位于`example/simple_container/mini_ue`
    - 两种类型的ue功能分别为：
        - 功能1：`ue_post`用于模拟用户的上传功能，通过该接口可以命令用户传输一个待求逆运算的数据矩阵发送到指定的vnf节点。
        - 功能2：`ue_print`用于将用户接受到的数据矩阵打印出来
    - ue的具体功能是通过服务器启动指令中的`ue_type`参数来指定的
    - 用户可以参考该镜像的功能，编写自己的ue镜像，并将其部署在MiniSFC仿真器中（建议在`mini_ue`的基础上进行扩展减少意外错误，每次修改完代码后都需要重新构建镜像）。
    - 详细的ue镜像制作过程将在后续的步骤中介绍。
    
在MiniSFC运行过程中，每个容器被创建时都会具备两个IP地址：
- `10.0.*.*`：MiniSFC内容虚拟网络的地址，该地址用于容器间的通信，即SFC中UE与各个VNF之前的数据流通（矩阵数据的转发）。
- `172.17.*.*`:容器的控制地址，该地址用于宿主机与各个容器的通信，即MiniSFC向各个容器下达的控制指令（转发表即传输开始命令的下达）。
- 地址的分配和管理是由MiniSFC自动完成的，用户不需要关心具体的IP地址分配。

接下来介绍仿真脚本的具体编写过程。

## 准备工作

为了对每次仿真结果进行标记，MiniSFC提供了一个`Trace`类，该类可以记录仿真过程中产生的信息，并提供时间戳进行标记。

```python
from minisfc.trace import Trace

SIMULATION_ID = Trace.get_time_stamp()
```

### 步骤一：定义基底网络拓扑

首先，需要构建一个基底网络拓扑，即一个包含所有节点和链路的网络拓扑。这个拓扑可以是静态的，也可以是动态的。不论是静态的还是动态的，都需要包含以下几个元素才可完整定义基底网络所需的信息。

- 时间：一个时间序列，用于标记网络拓扑发生变化的时间点，该时间默认以秒为单位，支持浮点数精度。如果需要构建的是静态的网络拓扑，则时间序列只包含一个元素，即基底网络的建立时间0.0。如果需要构建的是动态的网络拓扑，则时间序列包含多个元素，即网络拓扑发生变化的时间点。MiniSFC会根据该信息来自动生成事件，标记网络拓扑此时发生了变化，并对网络进行相应的调整。

```python
topoTimeList = [0.0]
```

- 邻接矩阵字典：一个以时间为索引的邻接矩阵字典，用于描述网络运行过程中不同时间点的节点之间的连接关系。矩阵的行数和列数分别为节点的数量，矩阵中的元素表示节点i和节点j之间是否存在一条链路。该字典的键需要与时间序列中的元素严格一一对应。需要注意的是该邻接矩阵需包含自环，这么做是基于部署在同一个物理设置上的不同VNF可以通过内部链路进行通信。

```python
topoAdjMatDict = {0.0:np.array([[1,1,0],
                                [1,1,1],
                                [0,1,1]])}
```

- 链路权重矩阵字典：一个以时间为索引的链路权重矩阵字典，用于描述网络运行过程中不同时间点的链路的权重。矩阵的行数和列数分别为节点的数量，矩阵中的元素表示节点i和节点j之间的链路的权重。该字典的键需要与时间序列中的元素严格一一对应。该权值默认为两个节点之间的传播延迟，单位为毫秒。需要注意各个权值矩阵应与邻接矩阵中的元素一一对应。即基于这样一种假设，两个节点之间不存在链路是，其权值矩阵中的元素应该为0或无穷大（因为节点的可达性是基于邻接矩阵的，因此不影响服务的时延累计的计算）。

```python
topoWeightMatDict = {0.0:np.array([[0,20,0], # delay ms
                                   [20,0,10],
                                   [0,10,0]])}
```

- 节点资源字典：一个以时间为索引的节点资源字典，用于描述网络运行过程中不同时间点的节点的资源信息。字典的键为元组，包含时间和资源类型两个元素，值为一个列表，包含每个节点的资源信息。资源类型可以是CPU、内存等，具体取决于想要模拟的网络的资源类型。需要注意的是，资源信息的数量应该与节点的数量相匹配，即每个节点都应该有对应的资源信息。且时间信息应该与时间序列中的元素严格一一对应。

```python
topoNodeResourceDict = {(0.0,'cpu'):[2,4,2], # cores
                        (0.0,'ram'):[256,512,256]} # Memmory MB
```

- 链路资源字典：一个以时间为索引的链路资源字典，用于描述网络运行过程中不同时间点的链路的资源信息。字典的键为元组，包含时间和资源类型两个元素，值为一个矩阵，包含每个链路的资源信息。资源类型可以是带宽等，具体取决于想要模拟的网络的资源类型。需要注意的是，资源信息的数量应该与链路的数量相匹配，即每个链路都应该有对应的资源信息。且时间信息应该与时间序列中的元素严格一一对应。

```python
topoLinkResourceDict = {(0.0,'band'):np.array([[100,100,0], # bw Mbps
                                               [100,100,100],
                                               [0,100,100]])}
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

- 添加VNF模板：VNF在MiniSFC中被抽象为`VnfEm`类，该类包含了VNF的ID、CPU占用、内存占用、带宽占用等信息。`VnfManager`对象提供了`add_vnf_into_pool`方法，用于向其内部的VNF模板池中添加VNF模板。需要注意的是，VNF模板的ID必须是唯一的，且不能与其他VNF模板的ID重复。'vnf_cpu'的值应该是浮点数，表示VNF的CPU占用，单位为核数。'vnf_ram'的值应该是整数，表示VNF的内存占用，单位为MB。为了能够使得容器正常启动，因此需要设置'vnf_type'参数用于指定vnf的功能类型，'vnf_img'参数用于指定vnf的镜像名称，'vnf_cmd'参数用于指定vnf服务的启动指令，'vnf_port'参数用于指定vnf服务的监听端口。

```python
template_str = "python run_command.py --vnf_name=$vnf_name --vnf_type=$vnf_type --vnf_ip=$vnf_ip --vnf_port=$vnf_port --vnf_cpu=$vnf_cpu --vnf_ram=$vnf_ram --vnf_rom=$vnf_rom"

vnfEm_template = VnfEm(**{'vnf_id':0,'vnf_cpu':0.2,'vnf_ram':64,
                          'vnf_type':'vnf_matinv','vnf_img':'vnfserver:latest','vnf_cmd':template_str,'vnf_port':5000})
nfvManager.add_vnf_into_pool(vnfEm_template)
vnfEm_template = VnfEm(**{'vnf_id':1,'vnf_cpu':0.15,'vnf_ram':64,
                          'vnf_type':'vnf_matprint','vnf_img':'vnfserver:latest','vnf_cmd':template_str,'vnf_port':5000})
nfvManager.add_vnf_into_pool(vnfEm_template)
vnfEm_template = VnfEm(**{'vnf_id':2,'vnf_cpu':0.15,'vnf_ram':64,
                          'vnf_type':'vnf_gnb','vnf_img':'vnfserver:latest','vnf_cmd':template_str,'vnf_port':5000})
nfvManager.add_vnf_into_pool(vnfEm_template)
```

<mark>在上述参数中'vnf_img':'vnfserver:latest'镜像需要用户预先构建好</mark>

在`example/simple_container`目录下(与`Dockerfile.vnfserver`文件同一级)，运行

```bash
docker build -f Dockerfile.vnfserver -t vnfserver:latest .
```

<mark>构建完成后可在终端中运行'sudo docker images'进行检查</mark>


- 设置VNF间虚拟链路资源占用：`VnfManager`对象提供了`set_vnf_resource_info`方法，用于设置VNF间的虚拟链路资源占用信息。该方法需要三个参数，前两个参数为VNF的ID，第三个参数为资源占用信息。资源占用信息是一个字典，包含资源类型和占用量两个元素，资源类型默认支持单位为MB的带宽，具体取决于想要模拟的网络的资源类型。

```python
nfvManager.add_vnf_service_into_pool(2,0,**{"band":20})
nfvManager.add_vnf_service_into_pool(0,2,**{"band":20})
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
sfcIdList = [0,1]
```

- 生命周期：一个以SFC ID为索引的字典，用于描述SFC的生命周期。字典的键为SFC的ID，值为一个列表，包含两个元素，分别为SFC的建立时间和终止时间。该值以秒为单位，且生命周期的终止时间应该大于等于建立时间。MiniSFC会根据该信息来自动生成事件，调度每一个SFC的部署和终止，并在最后一个生命周期终止时停止仿真。需要注意的是，该字典的键需要与SFC ID列表中的元素严格一一对应。

```python
sfcLifeTimeDict = {0:[5,25],
                   1:[10,50]}
```

- 端点：一个以SFC ID为索引的字典，用于描述SFC的端点。端点的设置基于这样一种假设，即用户对其请求服务的接入接出点是基于用户与网络设施的相对物理位置的，当由于网络拓扑的变化而导致服务的接入接出点发生变化时，用户应当重新请求服务（此处是当前版本V2.0的权宜之计，后续版本将设计更符合实际情况的动态设置方法）。字典的键为SFC的ID，值为一个列表，包含SFC的接入接出点对应的基底网络上的物理节点ID。要注意的是，该字典的键需要与SFC ID列表中的元素严格一一对应。

```python
endPointDict = {0:[0,2],
                1:[0,1]}
```

- VNF请求：一个以SFC ID为索引的字典，用于描述SFC的VNF请求。字典的键为SFC的ID，值为一个列表，包含SFC所需的VNF的ID，其中的ID值即为VNF模板池中VNF模板的ID，列表的长度即为SFC所需的VNF数量，由于不同VNF的功能不同，因此该列表中允许出现相同的VNF ID，即使用一个VNF模版分别创建不同的实例进行部署。需要注意的是，该字典的键需要与SFC ID列表中的元素严格一一对应。

```python
vnfRequstDict = {0:[2,0,2],
                 1:[2,0,2]}
```

- 服务QoS需求：一个以SFC ID为索引的字典，用于描述SFC的QoS需求。字典的键为SFC的ID，值为一个列表，包含SFC的QoS需求，这里与基底网络中节点之间的传输时延对应，单位为毫秒，该值表示SFC的端到端时延要求。需要注意的是，该字典的键需要与SFC ID列表中的元素严格一一对应。

```python
qosRequesDict = {0:[100],
                 1:[100]}
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

### 步骤四：定义用户管理器

用户管理器的设计是基于这样一种假设，即对用户设备的模拟也通过容器进行封装和部署，因此用户管理器的设计与VNF管理器类似，即也将用户模型抽象为模版向系统中注册。进而在后续运行中，系统自动将用户与请求的SFC进行关联。MiniSFC作为整个仿真场景的总指挥，对网络中的包括用户在内的各个实体进行统一的管理和控制。

- 实例化：`UeManager`对象可以直接实例化，不需要任何参数。

```python
from minisfc.mano.uem import UeManager, Ue

ueManager = UeManager()
```

- 添加用户模板：用户在MiniSFC中被抽象为`Ue`类，该类包含了用户的ID、类型、镜像名称、启动指令、监听端口等信息。`UeManager`对象提供了`add_ue_into_pool`方法，用于向其内部的用户模板池中添加用户模板。需要注意的是，用户模板的ID必须是唯一的，且不能与其他用户模板的ID重复。'ue_type'的值应该是字符串，表示用户的类型，'ue_img'的值应该是字符串，表示用户的镜像名称，'ue_cmd'的值应该是字符串，表示用户服务的启动指令，'ue_port'的值应该是整数，表示用户行为被控指令的监听端口。

```python
template_str = "python run_command.py --ue_name=$ue_name --ue_type=$ue_type --ue_ip=$ue_ip --ue_port=$ue_port"

ue_template = Ue(**{'ue_id':0,'ue_type':'ue_post','ue_img':'ueserver:latest','ue_cmd':template_str,'ue_port':8000})
ueManager.add_ue_into_pool(ue_template)
ue_template = Ue(**{'ue_id':1,'ue_type':'ue_print','ue_img':'ueserver:latest','ue_cmd':template_str,'ue_port':8000})
ueManager.add_ue_into_pool(ue_template)
```
<mark>在上述参数中'ue_img':'ueserver:latest'镜像需要用户预先构建好</mark>

在`example/simple_container`目录下(与`Dockerfile.ueserver`文件同一级)，运行

```bash
docker build -f Dockerfile.ueserver -t ueserver:latest .
```

<mark>构建完成后可在终端中运行'sudo docker images'进行检查</mark>


- 设置用户请求：`UeManager`对象提供了`add_ue_service_into_pool`方法，用于设置用户请求的SFC的ID、请求延时等信息。该方法需要三个参数，前两个参数为用户的ID，第三个参数为请求信息。请求信息是一个字典，目前设置为请求的发送间隔，单位为秒。

```python
ueManager.add_ue_service_into_pool(0,1,**{"req_delay":0.1}) 
```

- 保存用户管理器：为了方便后续的仿真，可以将`UeManager`对象保存为一个pickle文件进行固化，即无需每次都重新构建该对象，该方法适用于构建随机网络拓扑的场景并测试不同算法的性能时，进行变量控制。

```python
with open(f"{ueManager.__class__.__name__}_{SIMULATION_ID}.pkl", "wb") as file:
    pickle.dump(ueManager, file)
```


### 步骤五：定义SFC部署求解器

MiniSFC提供了多种SFC部署求解器，用于求解SFC在基底网络上的部署方案。在仿真之前，需要选择一个部署求解器，该求解器可以来自于Minisfc的`SfcSolver`类例如`RandomSolver`、`GreedySolver`等，也可以来自于用户集成了Minisfc的`SfcSolver`类后实现的自定义求解器，例如`PsoSolver`。

`SfcSolver`对象的实例化需要两个参数，第一个参数为`SubstrateTopo`对象，第二个参数为`ServiceTopo`对象，这两个对象分别代表了基底网络拓扑和SFC拓扑，可用于求解器的初始化。因此我们默认求解器具备未来网络发生事件的全部信息，因此可用于基于学习类的预测算法。当然如果用户希望实现一个完全基于突发事件的求解器，则可以忽略掉这两个参数，而是仅根据事件发生时的信息进行计算。

```python
from minisfc.solver import RandomSolver, GreedySolver
from custom.psoSolver import PsoSolver

sfcSolver = RadomSolver(substrateTopo,serviceTopo)
```

### 步骤六：定义MiniSFC仿真器

MiniSFC提供了`Minisfc`类来进行仿真，该类包含了仿真的主要逻辑，包括事件驱动、事件处理、事件调度、仿真结果记录等。

`Minisfc`对象的实例化需要六个参数，第一个参数为`SubstrateTopo`对象，第二个参数为`ServiceTopo`对象，第三个参数为`VnfManager`对象，第四个参数为`SfcSolver`对象，第五个参数为`UeManager`对象，第六个参数为布尔值，表示是否使用容器模拟，默认为`True`。

```python
from minisfc.net import Minisfc

net = Minisfc(substrateTopo,serviceTopo,nfvManager,sfcSolver,ueManager=ueManager,use_container=True)
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

<mark>在运行仿真之前，这里需声明一下SDN控制器的问题</mark>

由于MiniSFC的基于容器的仿真是基于`Containernet`实现的，而`Containernet`默认使用了`Mininet`中的简单控制器作为SDN控制器，该控制器的流表下发功能仅能支持简单的匹配规则，因此仅能工作在树状拓扑结构的网络中，而无法处理有环的网络拓扑。具体的表现形式即为创建了模拟vnf的容器后，各个容器之间无法正常通信，导致用户的请求无法到达目的地。因此为了解决该问题，MiniSFC支持用户使用自定义的SDN控制器，并将其部署在仿真环境中。

MiniSFC将`Containernet`的添加外部控制器功能封装为`addRemoteController`方法，该方法需要三个参数，第一个参数为控制器的名称，第二个参数为控制器的IP地址，第三个参数为控制器的端口。

```python
net.addRemoteController(self,name='c0', ip='127.0.0.1', port=6653):
```

如果用户对RYU控制器的使用较为了解，可以直接使用路径`examples/simple_container/ryu/simple_switch_stp_13.py`脚本来启动RYU控制器提供的一个基于STP协议的控制器应用，可以实现剪枝算法进而解决环路问题。具体流程为：
 - 安装RYU控制器，具体方法可参考[Ryu 安装教程](https://www.yuque.com/wangxi_chn/kozrfl/ov20zsfgpt4naaki#)
 - 使用RYU控制器加载`simple_switch_stp_13.py`应用脚本
 - 在MiniSFC的场景脚本中，调用`addRemoteController`方法，将RYU控制器的IP地址和端口号作为参数传入
 - 启动仿真，由于STP协议需要较长的时间用来学习拓扑，因此建议将首个SFC的到达时间适当延长，以便让控制器学习完拓扑后再开始部署SFC

<mark>如何将控制器流表下发功能集成在MiniSFC中，并解决环路问题，将在后续版本中进行完善</mark>

上述工作完成后，就可以启动仿真，该过程会自动生成事件并进行调度，直到所有SFC的生命周期终止。`net.stop()`在基于容器的模拟仿真中，该方法是必须的，因为需要该方法释放仿真过程中所占用的资源并退出Containernet仿真环境，避免对下次仿真造成影响。为了避免仿真过程中的意外中断导致Containernet环境无法正常退出，建议将`net.stop()`放置在try-except语句中，捕获异常并调用`net.stop()`方法进行清理。

```python
try:
    net.start()
    net.stop()
except Exception as e:
    net.stop()
    raise e
```

由于基于容器的仿真需要用到Docker指令因此会强制要求运行该脚本的用户具有root权限，在使用`sudo`命令时，需要提前通过`which`命令找到`python`的路径，并将其替换为`sudo path/to/python`。

如果使用示例中的默认脚本，则运行如下命令：

```bash
cd minisfc/examples/simple_dynamictopo
which python
sudo path/to/python simple_dynamictopo.py
```

如果使用了Anaconda环境（例如命名为`minisfc`的开发环境），则运行如下命令：

```bash
cd minisfc/examples/simple_dynamictopo
conda activate minisfc
which python
sudo path/to/python simple_dynamictopo.py
```

## 仿真过程

在仿真运行过程中，会在执行该脚本中的终端创建一个基于`tqdm`的进度条，显示仿真的进度。该进度条会显示当前仿真时间、当前仿真事件等信息。可用于观察仿真的运行情况，以及当仿真突然中断时，可以根据进度条信息来进行调试。

由于MiniSFC工作在基于容器的仿真环境中，因此在运行时，会自动弹出两个执行监控任务的终端窗口：
- 窗口1：用于实时将各个容器的记录日志拷贝到当前目录下的`logsave`文件夹中，并实时显示在该窗口中。
    - 该`logsave`文件夹中的存放内容为以仿真过程中动态创建的以vnf名称命名的.log文件，记录了每个容器中数据包的收发情况。记录条目为`时间,行为（+为接收，-为发送）,PacketID`，便于后续追踪每个数据包在各个环节的用时。
    - 所自动执行的采集脚本存放于`minisfc/util/auto_getlogs.sh`中，用户可以根据自己的需求进行修改。
- 窗口2：用于实时将各个容器的CPU、内存占用情况保存在当前目录下的`logsave`文件夹中，并实时显示在该窗口中。
    - 该文件的命名为`vnf_stats.log`,记录的条目为`时间戳\t容器名称\tCPU占用\t内存占用`，便于后续分析各个节点的负载情况。
    - 所自动执行的采集脚本存放于`minisfc/util/auto_getstatus.sh`中，用户可以根据自己的需求进行修改。

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

以及来源于自动采集脚本的日志文件夹`logsave`，该文件夹中包含了每个容器的日志文件。

用户可以根据自己的需求对日志文件进行分析，例如绘制仿真结果图表、分析SFC部署失败的原因、分析资源的分配情况等。

MiniSFC提供了一个简易的分析模块`DataAnalysis`，可以帮助用户快速分析日志文件，在每次仿真结束后，该模块会自动打印一行文字输出SFC部署成功率等信息，用户可以根据该信息快速判断算法的性能。

```python
from minisfc.util import DataAnalysis
DataAnalysis.getResult(TraceResultFile)
```

在`examples/simple_container`目录下提供了两个基于`matplotlib`的仿真结果分析示例：
- `draw_nvfi_statues_numerical.py`：即便MiniSFC工作在基于容器的仿真环境中，但也会保留基于数值仿真的仿真结果，因此可以通过该脚本绘制在理想状态下，各个节点的CPU、内存占用情况，如下图所示。

![nvfi_status_numerical](https://raw.githubusercontent.com/wangxichn/image_hosting/d9ae503b3848bfdc16bfa50ca6ff13fcc9573cdc/minisfc/Draw_simple_dynamictopo_nvfi_statues_with_numerical_data.svg)

- `draw_nvfi_statues_container.py`：该脚本的功能同样是绘制各个节点的CPU、内存占用情况，但是其数据来源于容器的日志文件，因此真实准确的反映了各个节点的实际资源占用情况，如下图所示。

![nvfi_status_numerical](https://raw.githubusercontent.com/wangxichn/image_hosting/d9ae503b3848bfdc16bfa50ca6ff13fcc9573cdc/minisfc/Draw_simple_dynamictopo_nvfi_statues_with_container_data.svg)

示例中提供的`get_statstable.py`脚本，用于将日志文件`vnf_stats.log`中的数据提取和整理，并保存为csv文件，便于后续分析。

示例中提供的`get_logtable.py`脚本，用于将日志文件各个容器的日志文件`vnf*.log`中的数据提取和整理，并保存为csv文件，便于后续分析每个数据包在各个环节的用时。
