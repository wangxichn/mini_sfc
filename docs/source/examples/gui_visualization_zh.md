[中文](./gui_visualization_zh.md) | [English](./gui_visualization_en.md)

# 使用GUI将MiniSFC仿真结果可视化

在该示例中，我们将展示如何使用GUI将MiniSFC的仿真结果可视化。该可视化关注的是网络运行过程中不同时刻的节点资源的负载变化，包括CPU、内存等。

## 准备工作

MiniSFC的GUI工具是基于Python和PyQt5开发的，该工具的开发框架可以参考我们的另外一个项目[Netterminal](https://gitee.com/WangXi_Chn/netterminal)。在示例`example/gui_visualization`中，我们使用的GUI工具由该框架精简后得到，专为MiniSFC的仿真结果分析设计，去掉了框架中不必要的功能。

首先，需要通过示例中提供的setup.py文件安装必要的依赖, 在`example/gui_visualization`目录下运行如下命令：

```
pip install -e .
```

## 开始运行

运行如下命令启动GUI工具：

```
python Main.py
```

## 如何使用

可以参考下面的动画演示：

![gui_visualization.gif](https://raw.githubusercontent.com/wangxichn/image_hosting/refs/heads/main/minisfc/minisfc_example_gui_show.gif)

需要注意的是，使用该工具分析MiniSFC的仿真结果至少需要两个文件：
1. 仿真结果文件：该文件是MiniSFC关于节点资源的仿真结果，由MiniSFC的仿真器生成，文件格式为csv。通常默认为`TraceNFVI_算法名_仿真ID.csv`
2. 节点配置文件：该文件是MiniSFC的仿真中产生的节点数据文件，由MiniSFC的仿真脚本对`SubstrateTopo`类进行序列化后生成，文件格式为pkl。通常默认为`SubstrateTopo_仿真ID.pkl`

在GUI工具中，通过点击`选择文件`按键，在弹出的对话框中选择需要展示的.csv文件，程序将自动根据文件名后面的仿真ID自动选择合适的.pkl文件导入，因此选择的.csv文件和.pkl文件必须在同一目录下存放。
