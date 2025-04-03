[中文](./install_zh.md) | [English](./install_en.md)

# Installation

**注意**：对于希望灵活配置以及使用基于CUDA的人工智能算法进行研究的人员来说，裸机安装为最佳选择。确保您的机器运行Ubuntu **22.04 LTS**（其他版本未经测试），并已安装**Python3.10**及以上版本。

**Note**: For researchers who require flexible configuration and want to utilize CUDA-based AI algorithms, bare-metal installation is the recommended approach. Ensure your machine runs **Ubuntu 22.04 LTS** (other versions are untested) with **Python 3.10** or higher installed.

## Prerequisites

Note: If you plan to deploy Mini-SFC in an Anaconda virtual environment (e.g., a development environment named `minisfc`), the following installation steps should be performed after activating the virtual environment.

```bash
conda activate minisfc
```

Mini-SFC's container-based simulation functionality relies on the Containernet simulator, which requires Docker.

Please ensure Docker is installed on your system. For installation instructions, refer to:[Docker Tutorial and Resources](https://www.yuque.com/wangxi_chn/qaxke0/itdap183fetk0gza#)。

Then install Containernet. For installation guidance, see:[Containernet Installation and Configuration](https://www.yuque.com/wangxi_chn/kozrfl/ztp52q4k6l3974qh#)。

After verifying that Containernet's basic functions work properly, you may proceed with Mini-SFC installation.

## Installing Mini-SFC

First, clone the Mini-SFC repository:

```bash
git clone https://gitee.com/WangXi_Chn/mini_sfc.git

or

git clone https://github.com/wangxichn/mini_sfc.git
```

Then install the required dependencies using setup.py (recommended to use virtual environment with -e option for developer mode installation):

```bash
pip install -e .
```

After completing these steps, you can begin exploring Mini-SFC's features through the subsequent example documentation.

