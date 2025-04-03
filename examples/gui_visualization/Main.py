#Anaconda/envs/pyqtenv python
# -*- coding: utf-8 -*-
'''
@File    :   Main.py
@Time    :   2024/10/18 16:07:38
@Author  :   WangXi 
@Version :   1.0
@Desc    :   Built in PyQt5
             MiniSFC Gui 可用于仿真结果的可视化
'''

import sys
from PyQt5.QtWidgets import QApplication

from Netterminal.Sources.App.AppMiniSFC import AppMiniSFC

if __name__ == "__main__":
    styleFile = 'Netterminal/Forms/qss/MaterialDark.qss'
    with open(styleFile, 'r', encoding="utf-8") as f:
        qssStyle = f.read()
        
    app = QApplication(sys.argv)
    
    appMinisfc = AppMiniSFC()
    appMinisfc.setStyleSheet(qssStyle)
    appMinisfc.show()

    sys.exit(app.exec_())
    