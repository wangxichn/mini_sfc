#Anaconda/envs/pyqtenv python
# -*- coding: utf-8 -*-
'''
@File    :   DevBase.py
@Time    :   2024/10/18 19:07:04
@Author  :   CRC1109 
@Version :   1.0
@Desc    :   Built in PyQt5
'''

from PyQt5.QtCore import QObject

class DevBase(QObject):
    def __init__(self,name:str):
        super(DevBase,self).__init__()
        self.name = name

    def register(self):
        raise NotImplementedError("Subclasses should implement this!")
    
    def ready(self):
        raise NotImplementedError("Subclasses should implement this!")

    def open(self):
        raise NotImplementedError("Subclasses should implement this!")

    def close(self):
        raise NotImplementedError("Subclasses should implement this!")

    def read(self):
        raise NotImplementedError("Subclasses should implement this!")

    def write(self):
        raise NotImplementedError("Subclasses should implement this!")
    
    def ctl(self):
        raise NotImplementedError("Subclasses should implement this!")

