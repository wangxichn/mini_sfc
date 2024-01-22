#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   test_list_remove.py
@Time    :   2024/01/22 10:25:52
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''


list_a = [1, 2, 3, 4]

for item in list_a[:]:
    if item > 2:
        list_a.remove(item)

print(list_a)
