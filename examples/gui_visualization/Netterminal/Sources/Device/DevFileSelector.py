#Anaconda/envs/pyqtenv python
# -*- coding: utf-8 -*-
'''
DevFileSelector.py
==================

.. module:: DevFileSelector
  :platform: Windows, Linux
  :synopsis: 文件选择器模块,用于选择系统中指定文件

.. moduleauthor:: CRC1109-WangXi

简介
----

该模块实现了常见的选择系统中某个文件的功能：

- 使用***组件呈现***
- 支持基本***控制操作（如***、***、***等）。

版本
----

- 版本 1.0 (2025/03/31): 初始版本

'''

import os
import logging
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QPushButton, QFileDialog, QLineEdit

from Netterminal.Sources.Device.DevBase import DevBase

class DevFileSelector(DevBase):
    file_choosed_signal = pyqtSignal()
    def __init__(self,name:str,**kwargs):
        super(DevFileSelector,self).__init__(name)
        
        self.register(**kwargs)
        
        self.file_path = None
        
    
    def register(self,**kwargs):
        self.fileSelect_bushbutton:QPushButton = kwargs.get('fileSelect_bushbutton',None)
        if not isinstance(self.fileSelect_bushbutton, QPushButton):
            raise TypeError("传入的控件必须是 QPushButton 类")
        self.fileSelect_lineEdit:QLineEdit = kwargs.get('fileSelect_lineEdit',None)
        if not isinstance(self.fileSelect_lineEdit, QLineEdit):
            raise TypeError("传入的控件必须是 QLineEdit 类")
        

    def ready(self):
        self.fileSelect_bushbutton.clicked.connect(self.on_open_file_dialog)
        self.fileSelect_lineEdit.editingFinished.connect(self.on_lineEdit_changed)
        
    
    def ctl_set_file_path(self,file_path:str): 
        self.file_path = file_path
        self.fileSelect_lineEdit.setText(file_path)
        logging.info(f"{self.name} | 当前选择文件路径：{self.file_path}")
    
    
    @pyqtSlot()
    def on_open_file_dialog(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(None, "选择文件", os.getcwd(), "文本文件 (*.csv);;所有文件 (*)", options=options)
        if file_name:
            self.ctl_set_file_path(file_name)
            self.file_choosed_signal.emit()
            
            
    @pyqtSlot()
    def on_lineEdit_changed(self):
        self.ctl_set_file_path(self.fileSelect_lineEdit.text())
        self.file_choosed_signal.emit()

