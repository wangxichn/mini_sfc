#Anaconda/envs/pyqtenv python
# -*- coding: utf-8 -*-
'''
@File    :   MainWindowMin.py
@Time    :   2024/10/18 16:08:30
@Author  :   WangXi 
@Version :   1.0
@Desc    :   Built in PyQt5
             MiniSFC演示Gui主界面逻辑控制
             主界面设计文件为 App_MiniSFC.ui->Ui_App_MiniSFC.py
'''

import logging
import networkx as nx
import numpy as np
from PyQt5.QtWidgets import QMainWindow, QDesktopWidget
from PyQt5.QtCore import pyqtSlot

from Netterminal.Forms.Ui_App_MiniSFC import Ui_MainWindow_Minisfc
from Netterminal.Sources.Component.ComMinisfcDataFun import ComMinisfcDataFun
from Netterminal.Sources.Component.ComMinisfcShowFun import ComMinisfcShowFun

class AppMiniSFC(QMainWindow, Ui_MainWindow_Minisfc):
    def __init__(self, parent=None) -> None:
        super(AppMiniSFC,self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("MiniSFC GUI")

        screen = QDesktopWidget().screenGeometry()
        screenWidth = screen.width()
        screenHeight = screen.height()
        self.resize(int(screenWidth * 0.6), int(screenHeight * 0.9))
        
        logging.basicConfig(
            level=logging.ERROR,  # 设置全局日志级别
            format='%(asctime)s - %(levelname)s - %(message)s',
        )
        
        self.plt_background_color = [30/255, 29/255, 35/255]

        self.initComponent()
        
        self.ready()


    def initComponent(self):
        self.comMinisfcDataFun = ComMinisfcDataFun("MinisfcDataFun",
                                                   **{"fileSelect_lineEdit":self.fileSelect_lineEdit,
                                                      "fileSelect_bushbutton":self.fileSelect_bushbutton})
        
        self.comMinisfcShowFun = ComMinisfcShowFun("MinisfcShowFun",
                                                   **{"pltboard_widget":self.pltboard_widget,
                                                      "timeProcessSpeed_label":self.timeProcessSpeed_label,
                                                      "timeProcessCurrentTime_label":self.timeProcessCurrentTime_label,
                                                      "timeProcess_slider":self.timeProcess_slider,
                                                      "timeProcessPlay_button":self.timeProcessPlay_button,
                                                      "timeProcessRewind_button":self.timeProcessRewind_button,
                                                      "timeProcessFastRewind_button":self.timeProcessFastRewind_button,
                                                      "timeProcessForward_button":self.timeProcessForward_button,
                                                      "timeProcessFastForward_button":self.timeProcessFastForward_button,
                                                      "datatype_choose_comboBox":self.datatype_choose_comboBox})
        
    def ready(self):
        self.comMinisfcDataFun.data_ready_signal.connect(self.ready_for_show)
        self.comMinisfcShowFun.data_type_changed_signal.connect(self.data_type_changed)
        self.comMinisfcShowFun.devPltBoard.ctl_set_background_color(self.plt_background_color)

    
    @pyqtSlot()
    def ready_for_show(self):
        logging.info(f"Ready for show with time series: {self.comMinisfcDataFun.simulation_timeseries}")
        self.comMinisfcShowFun.devTimeProcess.ctl_set_time_series(self.comMinisfcDataFun.simulation_timeseries)
        self.comMinisfcShowFun.devTimeProcess.ctl_set_handle_by_time(self.update_pltboard_handle)
        
        
        init_time = self.comMinisfcDataFun.simulation_timeseries[0]
        self.comMinisfcDataFun.current_adjmatrix = self.comMinisfcDataFun.simulation_substrateTopo.plan_adjacencyMatDict[init_time]
        G = nx.from_numpy_array(self.comMinisfcDataFun.current_adjmatrix)
        
        nodes_load_type = self.comMinisfcShowFun.datatype_choose_comboBox.currentText()
        nodes_load_colors = self.comMinisfcDataFun.ctl_get_nodes_load_colors(init_time, nodes_load_type)
        
        self.comMinisfcDataFun.node_pos = nx.spring_layout(G)  # 布局算法
        self.comMinisfcShowFun.devPltBoard.ctl_clear_axes()
        nx.draw(
            G,
            pos=self.comMinisfcDataFun.node_pos,
            ax=self.comMinisfcShowFun.devPltBoard.ctl_get_axes(),
            with_labels=True,
            node_color=nodes_load_colors,
            node_size=800,
            font_size=10,
            font_weight="bold",
            edge_color="gray"
        )
        
        # 添加色条 仅添加一次即可
        if self.comMinisfcShowFun.devPltBoard.colorbar_inited is False:
            colors_bar = self.comMinisfcDataFun.ctl_load_to_rgb(np.linspace(0, 1, 256))
            self.comMinisfcShowFun.devPltBoard.ctl_add_color_bar(colors_bar, label="资源负载", font_size=15, font_color="white")
        
        self.comMinisfcShowFun.devPltBoard.ctl_set_background_color(self.plt_background_color)
        self.comMinisfcShowFun.devPltBoard.ctl_refresh()
        
        self.comMinisfcDataFun.data_ready_to_play = True
        
        
    @pyqtSlot()
    def data_type_changed(self):
        if len(self.comMinisfcShowFun.devTimeProcess.time_series) == 0:
            logging.error("资源数据为空，无法更新图形，请先选择文件并加载数据！")
            return
        current_time = self.comMinisfcShowFun.devTimeProcess.time_series[self.comMinisfcShowFun.devTimeProcess.current_time_index]
        self.update_pltboard_handle(current_time)
        
        
    def update_pltboard_handle(self, current_time):
        if self.comMinisfcDataFun.data_ready_to_play is False: return  # 数据未准备好，不更新图形
        adjmatrix = self.comMinisfcDataFun.simulation_substrateTopo.plan_adjacencyMatDict.get(current_time, None)
        if adjmatrix is not None: self.comMinisfcDataFun.current_adjmatrix = adjmatrix # 更新邻接矩阵
        if self.comMinisfcDataFun.current_adjmatrix is not None:
            G = nx.from_numpy_array(self.comMinisfcDataFun.current_adjmatrix)
            
            nodes_load_type = self.comMinisfcShowFun.datatype_choose_comboBox.currentText()
            nodes_load_colors = self.comMinisfcDataFun.ctl_get_nodes_load_colors(current_time, nodes_load_type)
            self.comMinisfcShowFun.devPltBoard.ctl_clear_axes()
            nx.draw(
                G,
                pos=self.comMinisfcDataFun.node_pos,
                ax=self.comMinisfcShowFun.devPltBoard.ctl_get_axes(),
                with_labels=True,
                node_color=nodes_load_colors,
                node_size=800,
                font_size=10,
                font_weight="bold",
                edge_color="gray"
            )
            self.comMinisfcShowFun.devPltBoard.ctl_set_background_color(self.plt_background_color)
            self.comMinisfcShowFun.devPltBoard.ctl_refresh()
            
        
        