#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   dataAnalysis.py
@Time    :   2024/06/20 21:03:17
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

import pandas as pd
import numpy as np
import code

class DataExtractor:
    def __init__(self,filename:str) -> None:
        self.filename = filename
    
    def extract(self,header:list[str]):
        data = pd.read_csv(self.filename)
        return(data[header])

class DataAnalysis:
    def __init__(self) -> None:
        pass
    
    @staticmethod
    def getResult(filename:str):
        dataExtractor = DataExtractor(filename)
        dataFrame = dataExtractor.extract(['Event','Result'])
        dataFrame_array = np.array(dataFrame)
        dataFrame_list = dataFrame_array.tolist()

        sfcNum = 0
        sfcSetNum = 0
        sfcCompleteNum = 0

        for i in range(len(dataFrame_list)):
            if dataFrame_list[i][0] == '+':
                sfcNum += 1
                if dataFrame_list[i][1] == True:
                    sfcSetNum += 1
            elif dataFrame_list[i][0] == '-':
                if dataFrame_list[i][1] == True:
                    sfcCompleteNum += 1
        
        assert sfcNum != 0, ValueError(f'No "+" event in {filename}')
        
        resultReportDict = {'sfcNum':sfcNum,
                            'sfcSetNum':sfcSetNum,
                            'sfcSetRate':sfcSetNum/sfcNum,
                            'sfcCompleteNum':sfcCompleteNum,
                            'sfcCompleteRate':sfcCompleteNum/sfcNum
                            }

        print(f'INFO:Analysis Trace| {resultReportDict}')

        return resultReportDict
            

        
        


    



