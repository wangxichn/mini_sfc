[English](./README_en.md) | [中文](./README_zh.md)

# Mini-SFC

<img align="left" width="100" height="100" style="margin: 2px 2px 0 0;" src="https://raw.githubusercontent.com/wangxichn/image_hosting/refs/heads/main/minisfc/minisfc_logo_light.drawio.png" />

Mini-SFC 是一个针对服务功能链(SFC)编排算法设计的仿真框架，该框架同时支持基于离散事件构建的纯数值仿真和基于真实时间的容器模拟仿真，特别适用于研究基于MANO架构的SFC部署与迁移问题。该仿真框架参考了诸多著名网络仿真工具的设计理念，如[NS-3](https://www.nsnam.org/)、[Mininet](https://github.com/mininet/mininet)、[Containernet](https://github.com/containernet/containernet)、[VirNE](https://github.com/GeminiLight/virne)、[mini-nfv](https://github.com/josecastillolema/mini-nfv)等，这里向以上项目的开发者表示感谢！

## 特性

- 以场景脚本、仿真引擎、算法模板、日志记录等模块化设计
- 支持纯数值仿真（更快速验证算法在大规模场景下的性能）和基于容器模拟仿真（更真实地模拟网络拓扑、链路、服务）
- 集成各种模板算法，以及支持用户使用提供的接口进行自定义算法
- 支持仿真运行过程中的拓扑结构，包括基底网络拓扑的变化、VNF节点的添加和移除等

## 安装指南

对于希望灵活配置以及使用基于CUDA的人工智能算法进行研究的人员来说，裸机安装为最佳选择。确保您的机器至少运行Ubuntu **22.04 LTS**及以上的版本，并已安装**Python3.10**及以上版本。

首先，克隆本项目仓库：

```bash
git clone https://gitee.com/WangXi_Chn/mini_sfc.git
```

或者

```bash
git clone https://github.com/wangxichn/mini_sfc.git
```

然后使用setup.py文件安装相关依赖库（建议使用虚拟环境以及-e选项进行开发者模式安装）：

```bash
pip install -e .
```

完成以上步骤后，您就可以开始探索Mini-SFC的功能了。


## 开始使用

使用Mini-SFC非常直观，类似于Mininet、Containernet等网络仿真工具的操作流程。

### 运行基本示例

#### 纯数值仿真示例

进入mini_sfc/examples/simple_dynamictopo/目录并执行如下命令以启动一个纯数值仿真的示例：

```bash
python simple_dynamictopo.py
```

#### 容器模拟仿真示例

进入mini_sfc/examples/simple_container/目录并执行如下命令以启动一个基于容器模拟仿真的示例：

由于容器模拟仿真需要安装Docker，请确保您的机器上已安装Docker。
同时该示例需要通过containernet库进行容器网络的模拟，请确保您的机器上已安装containernet。
由于该示例需要sudo权限，请通过which命令获取python的绝对路径并使用sudo运行该示例。

```bash
which python
sudo path/to/python simple_container.py
```

## 文档

关于Mini-SFC更详细的文档，请访问我们的[GitHub Pages](https://wangxichn.github.io/mini_sfc/)页面。

## 研究

如果您使用Mini-SFC进行了相关的科研工作，欢迎分享您的成果！

### 引用本框架

如果您发现Mini-SFC对您的研究有帮助，请引用我们的相关论文：

**[Drones, 2024] PSO "Based On Version 1.0 of Mini-SFC"**

```bibtex
@Article{drones8040117,
AUTHOR = {Wang, Xi and Shi, Shuo and Wu, Chenyu},
TITLE = {Research on Service Function Chain Embedding and Migration Algorithm for UAV IoT},
JOURNAL = {Drones},
VOLUME = {8},
YEAR = {2024},
NUMBER = {4},
ARTICLE-NUMBER = {117},
URL = {https://www.mdpi.com/2504-446X/8/4/117},
ISSN = {2504-446X},
DOI = {10.3390/drones8040117}
}
```

## 联系我们

### 项目支持

如果您有任何问题或建议，欢迎通过Gitee或GitHub的issue或PR进行反馈

### 开发者信息

Wang Xi

- 邮箱：<wangxi_chn@foxmail.com>
- 主页：<https://www.yuque.com/wangxi_chn>