#Anaconda/envs/pyqtenv python
# -*- coding: utf-8 -*-
'''
ComMinisfcShowFun.py
====================

.. module:: ComMinisfcShowFun
  :platform: Windows, Linux
  :synopsis: Minisfc仿真数据可视化功能组件模块

.. moduleauthor:: WangXi

简介
----


版本
----

- 版本 1.0 (2025/04/01): 初始版本

'''

from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import pyqtSlot, pyqtSignal

from Netterminal.Sources.Component.ComBaseFun import ComBaseFun
from Netterminal.Sources.Device.DevPltBoard import DevPltBoard
from Netterminal.Sources.Device.DevTimeProcess import DevTimeProcess

class ComMinisfcShowFun(ComBaseFun):
    data_type_changed_signal = pyqtSignal()
    def __init__(self, name, **kwargs):
        super().__init__(name)
        self.name = name
        
        self.register(**kwargs)
        self.ready()
        
    def register(self, **kwargs):
        self.datatype_choose_comboBox:QComboBox = kwargs.get('datatype_choose_comboBox', None)
        self.devPltBoard = DevPltBoard("PltBoard", **kwargs)
        self.devTimeProcess = DevTimeProcess("TimeProcess", **kwargs)
    
    def ready(self):
        self.datatype_choose_comboBox.addItems(["cpu", "ram"])
        self.datatype_choose_comboBox.setCurrentIndex(0)
        self.datatype_choose_comboBox.currentIndexChanged.connect(self.ctl_data_type_changed)
        self.devPltBoard.ready()
        self.devTimeProcess.ready()
        
    @pyqtSlot()
    def ctl_data_type_changed(self):
        self.data_type_changed_signal.emit()
        
