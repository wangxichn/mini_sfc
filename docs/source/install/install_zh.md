[中文](./install_zh.md) | [English](./install_en.md)

# 安装指南

**注意**：对于希望灵活配置以及使用基于CUDA的人工智能算法进行研究的人员来说，裸机安装为最佳选择。确保您的机器运行Ubuntu **22.04 LTS**（其他版本未经测试），并已安装**Python3.10**及以上版本。

## 准备工作

Mini-SFC的基于容器的仿真功能依赖于Containernet仿真器，而Containernet需要安装Docker。

因此，请确保您的机器上已安装Docker，安装过程可参考[Docker教程与资料](https://www.yuque.com/wangxi_chn/qaxke0/itdap183fetk0gza#)。

然后，安装Containernet，安装过程可参考[Containernet安装与配置](https://www.yuque.com/wangxi_chn/kozrfl/ztp52q4k6l3974qh#)。

如果测试Containernet示例中的基础功能正常，则可以继续安装Mini-SFC

## 安装Mini-SFC

首先，克隆Mini-SFC的项目仓库：

```bash
git clone https://gitee.com/WangXi_Chn/mini_sfc.git

or

git clone https://github.com/wangxichn/mini_sfc.git
```

然后使用setup.py文件安装相关依赖库（建议使用虚拟环境以及-e选项进行开发者模式安装）：

```bash
pip install -e .
```

完成以上步骤后，您就可以开始通过后续的示例文档探索Mini-SFC的功能了。

