#Anaconda/envs/pyqtenv python
# -*- coding: utf-8 -*-
'''
DevTimeProcess.py
=================

.. module:: DevTimeProcess
  :platform: Windows, Linux
  :synopsis: 时间进度控制模块

.. moduleauthor:: CRC1109-WangXi

简介
----

该模块实现了时间进度控制的功能。它提供了以下特性：

- 使用进度条呈现时间进度
- 支持基本时间控制操作（如暂停、恢复、停止、快进、快退等）。

版本
----

- 版本 1.0 (2025/04/01): 初始版本

'''


from PyQt5.QtWidgets import QPushButton, QSlider, QLabel
from PyQt5.QtCore import QTimer
import logging

from Netterminal.Sources.Device.DevBase import DevBase

class DevTimeProcess(DevBase):
    def __init__(self,name:str,**kwargs):
        """时间进度条控制器

        Args:
            name (str): 设备名称
            **kwargs: 传入控件以及初始化参数，包括：
                - timeProcessSpeed_label (QLabel): 速度显示标签控件
                - timeProcessCurrentTime_label (QLabel): 当前时间显示标签控件
                - timeProcess_slider (QSlider): 进度条控件
                - timeProcessPlay_button (QPushButton): 播放/暂停按钮控件
                - timeProcessRewind_button (QPushButton): 快退按钮控件
                - timeProcessFastRewind_button (QPushButton): 极速退按钮控件
                - timeProcessForward_button (QPushButton): 快进按钮控件
                - timeProcessFastForward_button (QPushButton): 极速进按钮控件
                - time_series (list): 时间序列, 非必须在kwargs中传入, 可通过方法ctl_set_time_series设置
                - handle_by_time (callable): 时间变化时调用的函数句柄, 将自动向该函数中传入当前时间,
                                            非必须在kwargs中传入, 可通过方法ctl_set_handle_by_time设置      
        """
        super().__init__(name)
        
        self.register(**kwargs)
        
        self.time_series:list = kwargs.get('time_series',[])
        self.current_time_index = 0
        self.handle_by_time = kwargs.get('handle_by_time',None)
        self.is_playing = False
        self.speed_factor = 1
        self.timer = QTimer()

    def register(self,**kwargs):
        self.speed_label:QLabel = kwargs.get('timeProcessSpeed_label',None)
        if not isinstance(self.speed_label,QLabel):
            raise ValueError(f"{self.__class__.__name__}传入的speed_label参数必须是QLabel类")
        
        self.current_time_label:QLabel = kwargs.get('timeProcessCurrentTime_label',None)
        if not isinstance(self.current_time_label,QLabel):
            raise ValueError(f"{self.__class__.__name__}传入的current_time_label参数必须是QLabel类")
        
        self.slider:QSlider = kwargs.get('timeProcess_slider',None)
        if not isinstance(self.slider,QSlider):
            raise ValueError(f"{self.__class__.__name__}传入的slider参数必须是QSlider类")
        
        self.play_button:QPushButton = kwargs.get('timeProcessPlay_button',None)
        if not isinstance(self.play_button,QPushButton):
            raise ValueError(f"{self.__class__.__name__}传入的play_button参数必须是QPushButton类")
        
        self.rewind_button:QPushButton = kwargs.get('timeProcessRewind_button',None)
        if not isinstance(self.rewind_button,QPushButton):
            raise ValueError(f"{self.__class__.__name__}传入的rewind_button参数必须是QPushButton类")
        
        self.fast_rewind_button:QPushButton = kwargs.get('timeProcessFastRewind_button',None)
        if not isinstance(self.fast_rewind_button,QPushButton):
            raise ValueError(f"{self.__class__.__name__}传入的fast_rewind_button参数必须是QPushButton类")
        
        self.forward_button:QPushButton = kwargs.get('timeProcessForward_button',None)
        if not isinstance(self.forward_button,QPushButton):
            raise ValueError(f"{self.__class__.__name__}传入的forward_button参数必须是QPushButton类")
        
        self.fast_forward_button:QPushButton = kwargs.get('timeProcessFastForward_button',None)
        if not isinstance(self.fast_forward_button,QPushButton):
            raise ValueError(f"{self.__class__.__name__}传入的fast_forward_button参数必须是QPushButton类")
    
    
    def ready(self):
        self.timer.timeout.connect(self.ctl_update_time)
        self.slider.valueChanged.connect(self.ctl_on_slider_change)
        self.play_button.clicked.connect(self.ctl_toggle_play_pause)
        self.rewind_button.clicked.connect(lambda: self.ctl_set_speed(self.speed_factor-2))
        self.fast_rewind_button.clicked.connect(lambda: self.ctl_set_speed(self.speed_factor-4))
        self.forward_button.clicked.connect(lambda: self.ctl_set_speed(self.speed_factor+2))
        self.fast_forward_button.clicked.connect(lambda: self.ctl_set_speed(self.speed_factor+4))
        
        self.current_time_label.setText("")
        self.slider.setEnabled(False)
        
        self.ctl_update_speed_label()
        self.ctl_update_ui()
        
        
    def ctl_set_time_series(self, time_series):
        """设置时间序列"""
        self.time_series = time_series
        
        self.slider.setEnabled(True)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(self.time_series)-1) # 这里可能会触发一次valueChanged事件
        self.slider.setSingleStep(1)
        self.slider.setPageStep(1)
        
        self.current_time_index = 0
        
        self.ctl_update_ui()
    
    
    def ctl_set_handle_by_time(self, handle_by_time):
        """设置时间变化时调用的函数句柄"""
        self.handle_by_time = handle_by_time
        
    def ctl_toggle_play_pause(self):
        """切换播放/暂停状态"""
        if self.time_series is None or len(self.time_series) == 0:
            logging.warning(f"{self.__class__.__name__}没有设置时间序列，无法播放/暂停")
            return
        elif self.handle_by_time is None:
            logging.warning(f"{self.__class__.__name__}没有设置时间变化时调用的函数句柄，无法播放/暂停")
            return
        
        if self.is_playing:
            self.timer.stop()
            self.play_button.setText("▶")
            self.slider.setEnabled(True)
        else:
            self.timer.start(1) 
            self.play_button.setText("⏸")
            self.slider.setEnabled(False)
        self.is_playing = not self.is_playing
        
        
    def ctl_set_speed(self, factor):
        """设置速度因子"""
        self.speed_factor = factor
        self.ctl_update_speed_label()
        if self.is_playing:
            self.ctl_toggle_play_pause()  # 停止当前计时器
            self.ctl_toggle_play_pause()  # 重新启动以应用新的速度因子


    def ctl_update_speed_label(self):
        """更新速度标签"""
        self.speed_label.setText(f"播放速率 {self.speed_factor}")


    def ctl_update_time(self):
        """推进时间"""
        delta = 1 if self.speed_factor > 0 else -1
        new_time_index = self.current_time_index + delta * abs(self.speed_factor)
        self.current_time_index = max(0, min(new_time_index, len(self.time_series)-1))
        self.handle_by_time(self.time_series[self.current_time_index]) # 此处外部代码处理当前时间
        self.ctl_update_ui()
        if self.current_time_index >= len(self.time_series)-1 or self.current_time_index <= 0:
            self.timer.stop()
            self.play_button.setText("▶")
            self.is_playing = False
            self.slider.setEnabled(True)


    def ctl_on_slider_change(self, value):
        """手动拖拽进度条时更新仿真时间"""
        if not self.is_playing:  # 避免与定时器冲突
            self.current_time_index = value
            self.current_time_index = max(0, min(self.current_time_index, len(self.time_series)-1))
            self.ctl_update_ui()
            self.handle_by_time(self.time_series[self.current_time_index]) # 此处外部代码处理当前时间


    def ctl_update_ui(self):
        """更新UI显示"""
        if self.time_series is None or len(self.time_series) == 0:
            logging.warning(f"{self.__class__.__name__}没有设置时间序列，无法更新时间信息")
            return
        self.current_time_label.setText(f"当前时间: {self.time_series[self.current_time_index]}")
        self.slider.setValue(self.current_time_index)
        