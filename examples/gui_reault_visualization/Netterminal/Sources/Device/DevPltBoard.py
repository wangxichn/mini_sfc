#Anaconda/envs/pyqtenv python
# -*- coding: utf-8 -*-
'''
DevPltBoard.py
==============

.. module:: DevPltBoard
  :platform: Windows, Linux
  :synopsis: Matplotlib绘图板模块, 可用于显示图表。

.. moduleauthor:: CRC1109-WangXi

简介
----

该模块实现了将Matplotlib绘图板嵌入到应用程序中的功能,它提供了以下特性:


版本
----

- 版本 1.0 (2025/03/31): 初始版本

'''


from PyQt5.QtWidgets import QVBoxLayout, QWidget

from Netterminal.Sources.Device.DevBase import DevBase

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.colors import ListedColormap
import platform
import os

system = platform.system()
if system == "Windows":
    font_paths = [
        "C:/Windows/Fonts/simhei.ttf",  # 黑体
        "C:/Windows/Fonts/msyh.ttc"     # 微软雅黑
    ]
elif system == "Linux":
    font_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # 思源黑体
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"             # 文泉驿正黑
    ]
else:
    raise OSError("Unsupported operating system")

# 找到第一个存在的字体路径
font_path = None
for path in font_paths:
    if os.path.exists(path):
        font_path = path
        break

if not font_path:
    raise FileNotFoundError(f"{os.path.abspath(__file__)},No valid font found in the specified paths.")

font = FontProperties(fname=font_path)

# 设置全局字体属性
plt.rcParams['font.family'] = font.get_name()
plt.rcParams['font.sans-serif'] = [font.get_name()]
plt.rcParams['axes.unicode_minus'] = False    # 解决负号 '-' 显示为方块的问题

class DevPltBoard(DevBase):
    def __init__(self, name: str, **kwargs):
        super().__init__(name)
        
        self.register(**kwargs)
        
        self.canvas = None  # Matplotlib 画布
        self.toolbar = None # Matplotlib 工具栏
        self.figure = None  # Matplotlib 图形对象
        self.ax = None      # Matplotlib 坐标轴对象
        
        self.colorbar_inited = False  # 色条是否已经初始化

    def register(self, **kwargs):
        self.pltboard_widget: QWidget = kwargs.get('pltboard_widget', None)
        if not isinstance(self.pltboard_widget, QWidget):
            raise TypeError(f"{self.__class__.__name__}传入的pltboard_widget参数必须是QWidget类")

    def ready(self):
        """初始化画板，创建 Matplotlib 画布和工具栏"""
        # 清除外部控件的现有布局（如果有的话）
        layout = self.pltboard_widget.layout()
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            layout = QVBoxLayout()
            self.pltboard_widget.setLayout(layout)

        
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self.pltboard_widget)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self.ax.text(
            0.5, 0.5, "等待导入数据",  # 文本内容
            fontsize=30,              # 字体大小
            color="gray",             # 字体颜色
            ha="center",              # 水平对齐方式
            va="center",              # 垂直对齐方式
            transform=self.ax.transAxes  # 使用轴坐标系 (0,0) 到 (1,1)
        )

        # 隐藏坐标轴
        self.ax.set_xticks([])  # 隐藏 X 轴刻度
        self.ax.set_yticks([])  # 隐藏 Y 轴刻度
        self.ax.spines["top"].set_visible(False)    # 隐藏顶部边框
        self.ax.spines["right"].set_visible(False)  # 隐藏右侧边框
        self.ax.spines["left"].set_visible(False)   # 隐藏左侧边框
        self.ax.spines["bottom"].set_visible(False) # 隐藏底部边框

        self.canvas.draw()
    
    def ctl_update_figure(self, figure: Figure):
        """
        更新画板，使用外部传入的 Figure 对象。
        :param figure: 外部绘制好的 matplotlib.figure.Figure 对象
        """
        if not isinstance(figure, Figure):
            raise TypeError("传入的参数必须是 matplotlib.figure.Figure 类型")

        self.figure = figure

        # 清除现有的画布内容
        if self.canvas is not None:
            layout = self.pltboard_widget.layout()
            if layout is not None:
                # 移除旧的画布和工具栏
                layout.removeWidget(self.toolbar)
                layout.removeWidget(self.canvas)
                self.toolbar.deleteLater()
                self.canvas.deleteLater()

        # 使用新的 Figure 对象创建新的画布
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self.pltboard_widget)

        # 将新的画布和工具栏添加到布局中
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # 刷新画布
        self.canvas.draw()
        
        
    def ctl_update_data(self, x_data, y_data, **kwargs):
        """更新画板内容，支持指定绘制函数和参数

        Args:
            x_data (array-like): 新的 X 轴数据
            y_data (array-like): 新的 Y 轴数据
            kwargs (dict): 可选参数，包括：
                - plot_func (str): 绘制函数名，例如 'plot'、'scatter'
                - plot_kwargs (dict): 绘制函数的额外参数
                - title (str): 新的标题（可选）
                - xlabel (str): 新的 X 轴标签（可选）
                - ylabel (str): 新的 Y 轴标签（可选）
                - legend (str): 新的图例（可选）
        
        Examples:
            >>> x = np.linspace(0, current_time, current_time)
            >>> y = np.sin(x)
            
            >>> devPltBoard.ctl_update_data(
            >>>     x_data=x,
            >>>     y_data=y,
            >>>     plot_func="plot",
            >>>     plot_kwargs={"color": "red", "label": "Sine Wave"},
            >>>     title="Scatter Plot Example",
            >>>     xlabel="Time (s)",
            >>>     ylabel="Amplitude",
            >>>     legend="Sine Wave")
        """
        
        if self.ax is None or self.canvas is None:
            raise RuntimeError("画板未正确初始化，请先调用 ready() 方法")

        # 清除旧的绘图内容
        self.ax.clear()

        # 获取绘制函数名称和参数
        plot_func_name = kwargs.get("plot_func", "plot")  # 默认使用 'plot'
        plot_kwargs = kwargs.get("plot_kwargs", {})       # 默认为空字典

        # 动态调用绘制函数
        if hasattr(self.ax, plot_func_name):
            plot_func = getattr(self.ax, plot_func_name)
            plot_func(x_data, y_data, **plot_kwargs)
        else:
            raise ValueError(f"不支持的绘制函数: {plot_func_name}")

        # 设置标题、轴标签和图例
        if "title" in kwargs:
            self.ax.set_title(kwargs["title"])
        if "xlabel" in kwargs:
            self.ax.set_xlabel(kwargs["xlabel"])
        if "ylabel" in kwargs:
            self.ax.set_ylabel(kwargs["ylabel"])
        if "legend" in kwargs:
            self.ax.legend([kwargs["legend"]], loc="upper right")

        # 刷新画布
        self.canvas.draw()

    def ctl_refresh(self):
        """刷新画板"""
        if self.canvas is not None:
            self.canvas.draw()
    
    def ctl_clear_axes(self):
        """清除画板上的所有内容"""
        if self.ax is not None:
            self.ax.clear()
            self.canvas.draw()
    
    def ctl_get_axes(self):
        """获取画板上的坐标轴对象"""
        return self.ax

    def ctl_set_background_color(self, color):
        """设置画板背景颜色"""
        if self.ax is not None:
            self.ax.set_facecolor(color)
        if self.figure is not None:
            self.figure.set_facecolor(color)
        self.canvas.draw()

    def ctl_add_color_bar(self, colors, label = "Color Bar", font_size=10, font_color="black"):
        """在图中添加色条

        Args:
            colors (list[list[float]]): [[r,g,b],[r,g,b],...]不同数值的渐变颜色列表
        """
        if not self.colorbar_inited:
            self.colorbar_inited = True
        
            custom_cmap = ListedColormap(colors)
            
            # 创建一个标量映射对象
            norm = plt.Normalize(0, 1)  # 归一化到 [0, 1]
            
            # 添加色条
            sm = plt.cm.ScalarMappable(cmap=custom_cmap, norm=norm)
            sm.set_array([])  # 仅用于 colorbar
            cbar = plt.colorbar(sm, ax=self.ax, orientation='vertical', shrink=0.8)
            cbar.set_label(label, fontsize=font_size, color=font_color)
            cbar.ax.tick_params(labelsize=font_size, labelcolor=font_color)
