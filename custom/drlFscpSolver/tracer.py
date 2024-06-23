#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   tracer.py
@Time    :   2024/06/23 19:48:07
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   Ref. https://github.com/GeminiLight/drl-sfcp
             DRL-SFCP: Adaptive Service Function Chains Placement with Deep Reinforcement Learning
             By Wang, Tianfu and Fan, Qilin and Li, Xiuhua and Zhang, Xu and Xiong, Qingyu and Fu, Shu and Gao, Min
'''


import os
import csv
from .subenv import SubEnv
import torch
import time

class SolverPerf:
    """Trace the solver result
    """
    def __init__(self) -> None:
        self.SOLVER_TIME = None
        self.SOLVER_RESUALT = None
        self.SOLVER_RESUALT_NODE = None
        self.SOLVER_RESUALT_LINK = None
        self.SOLVER_ACTIONS = None
        self.SOLVER_REWARD = None

        self.LEARN_LR = None
        self.LEARN_LOSS = None
        self.LEARN_ACTOR_LOSS = None
        self.LEARN_CRITIC_LOSS = None
        self.LEARN_ENTROPY_LOSS = None
        self.LEARN_LOGPROB = None
        self.LEARN_RETURN = None

class SolverTracer:
    def __init__(self) -> None:

        run_time = time.strftime('%Y%m%dT%H%M%S')
        self.save_file = f"DrlFscpSolver_Perf_{run_time}.csv"
        self.model_file = f"DrlFscpSolver_Model_{run_time}.pkl"

    def handle_data(self,subenv: SubEnv = None,learning_info: dict = None):
        data_save = SolverPerf()

        if subenv != None:
            data_save.SOLVER_TIME = subenv.time
            data_save.SOLVER_RESUALT = subenv.subsolution.result
            data_save.SOLVER_RESUALT_NODE = subenv.subsolution.place_result
            data_save.SOLVER_RESUALT_LINK = subenv.subsolution.route_result
            data_save.SOLVER_ACTIONS = subenv.subsolution.selected_actions
            data_save.SOLVER_REWARD = subenv.subsolution.reward
        
        if learning_info != None:
            data_save.LEARN_LR = learning_info.get('lr',None)
            data_save.LEARN_LOSS = learning_info.get('loss/loss',None)
            data_save.LEARN_ACTOR_LOSS = learning_info.get('loss/actor_loss',None)
            data_save.LEARN_CRITIC_LOSS = learning_info.get('loss/critic_loss',None)
            data_save.LEARN_ENTROPY_LOSS = learning_info.get('loss/entropy_loss',None)
            data_save.LEARN_LOGPROB = learning_info.get('value/logprob',None)
            data_save.LEARN_RETURN = learning_info.get('value/return',None)

        self.__save_record(data_save)
    
    def save_model(self,**kwargs):
        torch.save({
            'policy': kwargs['policy'], # self.policy.state_dict(),
            'optimizer': kwargs['optimizer'] # self.optimizer.state_dict(),
        }, self.model_file)
        print(f'Save model to {self.model_file}\n')

    def load_model(self):
        print('Attempting to load the pretrained model')
        # current_directory = os.path.dirname(os.path.abspath(__file__))
        current_directory = os.path.abspath('.')
        model_file_list = []
        for filename in os.listdir(current_directory):
            if filename.endswith('.pkl'):
                model_file_list.append(filename)

        try:
            model_file = current_directory+"/"+model_file_list[-1]
            checkpoint = torch.load(model_file)
            print(f'Loaded pretrained model from {model_file_list[-1]}')
            return checkpoint['policy'],checkpoint['optimizer']
        except Exception as e:
            print(f'Load failed, Initilized with random parameters')
            return None,None


    def __save_record(self,save_data:SolverPerf):
        head = None if os.path.exists(self.save_file) else list(save_data.__dict__.keys())
        with open(self.save_file, 'a+', newline='') as csv_file:
            writer = csv.writer(csv_file, dialect='excel', delimiter=',')
            if head is not None: writer.writerow(head)
            writer.writerow(list(save_data.__dict__.values()))


