#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   main.py
@Time    :   2024/01/11 17:41:01
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

import logging
import code
import numpy as np

from data import Config
from base import Scenario

def run(config):
    logging.info(f"{'-' * 20}   Mini-SFC Start!   {'-' * 20}")

    scenario = Scenario.build(config)

    scenario.start()

    logging.info(f"{'-' * 20}   Mini-SFC Complete!   {'-' * 20}")

    # code.interact(banner="",local=locals())

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info(f"{'-' * 20}   Hello Mini-SFC!   {'-' * 20}")

    setting_files = ["setting_changetimes_10.yaml","setting_changetimes_20.yaml","setting_changetimes_30.yaml",
                     "setting_changetimes_40.yaml","setting_changetimes_50.yaml"]

    for file in setting_files:
        config = Config(**{"setting_file_name":file})
        run(config)

