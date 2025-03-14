#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   drlSfcpSolver.py
@Time    :   2024/06/23 16:22:22
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   Ref. https://github.com/GeminiLight/drl-sfcp
             DRL-SFCP: Adaptive Service Function Chains Placement with Deep Reinforcement Learning
             By Wang, Tianfu and Fan, Qilin and Li, Xiuhua and Zhang, Xu and Xiong, Qingyu and Fu, Shu and Gao, Min
'''

import sys
sys.path.append("..//..//")
from minisfc.event import Event
from minisfc.topo import ServiceTopo, SubstrateTopo, Topo
from minisfc.solver import RadomSolver, Solution, SOLUTION_TYPE
import code
import random
import copy 
import numpy as np
from .net import ActorCritic, apply_mask_to_logit
from .buffer import RolloutBuffer
from .subenv import SubEnv, SubSolution
from .tracer import SolverTracer
import torch
import torch.nn.functional as F
from torch.distributions import Categorical
import networkx as nx

class DrlSfcpSolver(RadomSolver):
    def __init__(self, substrateTopo: SubstrateTopo, serviceTopo: ServiceTopo, **kwargs) -> None:
        super().__init__(substrateTopo, serviceTopo)

        self.use_cuda = kwargs.get('use_cuda', True)
        if self.use_cuda and torch.cuda.is_available():
            print(f'INFO: {self.__class__.__name__} is using CUDA GPU')
            self.device = torch.device('cuda:0')
        else:
            print(f'INFO: {self.__class__.__name__} is using CPU')
            self.device = torch.device('cpu')

        self.buffer = RolloutBuffer()

        self.policy = ActorCritic(p_net_num_nodes=len(substrateTopo.nodes), 
                                  p_net_feature_dim=6, v_net_feature_dim=3, 
                                  embedding_dim=64).to(self.device)
        
        self.optimizer = torch.optim.Adam([
                {'params': self.policy.actor.parameters(), 'lr': 0.005},
                {'params': self.policy.critic.parameters(), 'lr': 0.001},
            ],
        )

        self.tracer = SolverTracer()
        
    def select_action(self, observation, mask=None, sample=True):
        with torch.no_grad():
            action_logits = self.policy.act(observation)

        if mask is not None:
            candicate_action_logits = apply_mask_to_logit(action_logits, mask) 
            candicate_action_probs = F.softmax(candicate_action_logits, dim=-1)
            candicate_action_dist = Categorical(probs=candicate_action_probs)
        else:
            candicate_action_logits = action_logits
            candicate_action_probs = F.softmax(action_logits, dim=-1)
            candicate_action_dist = Categorical(probs=candicate_action_dist)

        if sample:
            action = candicate_action_dist.sample()
        else:
            action = candicate_action_logits.argmax(-1)

        action_logprob = candicate_action_dist.log_prob(action)
        action = action.reshape(-1, )
        # action = action.squeeze(-1).cpu()
        return action.cpu().detach().numpy(), action_logprob.cpu().detach().numpy()
    

    def merge_experience(self,subsolution:SubSolution,subbuffer:RolloutBuffer):
        if subsolution.result == True:
            subbuffer.compute_mc_returns(gamma=0.95)
            self.buffer.merge(subbuffer)
        else:
            pass
    
    def update(self):
        observations = SubEnv.p_net_obs_to_tensor(self.buffer.observations, self.device)
        actions = torch.LongTensor(np.concatenate(self.buffer.actions, axis=0)).to(self.device)
        returns = torch.FloatTensor(self.buffer.returns).to(self.device)
        if len(self.buffer.action_mask) != 0:
            masks = torch.IntTensor(np.concatenate(self.buffer.action_mask, axis=0)).to(self.device)
        else:
            masks = None

        values, action_logprobs, dist_entropy, other = self.evaluate_actions(observations, actions, masks=masks, return_others=True)

        advantages = returns - values.detach()
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        actor_loss = - (action_logprobs * advantages).mean()
        critic_loss = F.mse_loss(returns, values)
        entropy_loss = dist_entropy.mean()
        loss = actor_loss + 0.5 * critic_loss + 0.01 * entropy_loss

        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy.parameters(), max_norm=1)
        self.optimizer.step()

        learning_info = {
            'lr': self.optimizer.defaults['lr'],
            'loss/loss': loss.detach().cpu().numpy(),
            'loss/actor_loss': actor_loss.detach().cpu().numpy(),
            'loss/critic_loss': critic_loss.detach().cpu().numpy(),
            'loss/entropy_loss': entropy_loss.detach().cpu().numpy(),
            'value/logprob': action_logprobs.detach().mean().cpu().numpy(),
            'value/return': returns.detach().mean().cpu().numpy()
        }

        self.buffer.clear()

        self.tracer.handle_data(None,learning_info)

        return loss
    
    def evaluate_actions(self, old_observations, old_actions, masks=None, return_others=False):
        actions_logits = self.policy.act(old_observations)
        actions_probs = F.softmax(actions_logits / 1, dim=-1)

        if masks is not None:
            candicate_actions_logits = apply_mask_to_logit(actions_logits, masks)
        else:
            candicate_actions_logits = actions_logits

        candicate_actions_probs = F.softmax(candicate_actions_logits, dim=-1)

        dist = Categorical(actions_probs)
        candicate_dist = Categorical(candicate_actions_probs)
        policy_dist = candicate_dist

        action_logprobs = policy_dist.log_prob(old_actions)
        dist_entropy = policy_dist.entropy()

        values = self.policy.evaluate(old_observations).squeeze(-1) if hasattr(self.policy, 'evaluate') else None

        if return_others:
            other = {}
            if masks is not None:
                mask_actions_probs = actions_probs * (~masks.bool())
                other['mask_actions_probs'] = mask_actions_probs.sum(-1).mean()
                if hasattr(self.policy, 'predictor'):
                    predicted_masks_logits = self.policy.predict(old_observations)
                    print(predicted_masks_logits)
                    prediction_loss = F.binary_cross_entropy(predicted_masks_logits, masks.float())
                    other['prediction_loss'] = prediction_loss
                    predicted_masks = torch.where(predicted_masks_logits > 0.5, 1., 0.)
                    correct_count = torch.eq(predicted_masks.bool(), masks.bool()).sum(-1).float().mean(0)
                    acc = correct_count / predicted_masks.shape[-1]
                    print(prediction_loss, correct_count, acc)
            return values, action_logprobs, dist_entropy, other

        return values, action_logprobs, dist_entropy
    
    def learn(self,event: Event,solution:Solution):
        self.subbuffer = RolloutBuffer()
    
        self.subenv = SubEnv(copy.deepcopy(event),copy.deepcopy(solution))
        subenv_obs = self.subenv.get_observation()
        subenv_done = False

        v_net_obs_tensor = SubEnv.v_net_obs_to_tensor(subenv_obs,self.device)
        encoder_outputs = self.policy.encode(v_net_obs_tensor)
        # remove dim 1 & to CPU & detach the tensor from the current calculation graph & change to numpy
        encoder_outputs = encoder_outputs.squeeze(1).cpu().detach().numpy()

        subenv_obs = {
            'p_net_x': subenv_obs['p_net_x'],
            'p_net_edge': subenv_obs['p_net_edge'],
            'p_net_node': len(self.subenv.p_net.nodes),
            'hidden_state': self.policy.get_last_rnn_state().squeeze(0).cpu().detach().numpy(),
            'encoder_outputs': encoder_outputs
        }

        while not subenv_done:
            hidden_state = self.policy.get_last_rnn_state()
            mask = np.expand_dims(self.subenv.get_action_mask(), axis=0)
            p_net_obs_tensor = SubEnv.p_net_obs_to_tensor(subenv_obs,self.device)
            action, action_logprob = self.select_action(p_net_obs_tensor, mask=mask, sample=True)
            value = self.policy.evaluate(p_net_obs_tensor).squeeze(-1).detach().cpu()

            next_subenv_obs, subenv_reward, subenv_done, subenv_info = self.subenv.step(action[0])

            p_node_id = action[0].item()

            self.subbuffer.add(subenv_obs,action,subenv_reward,subenv_done,action_logprob,value=value)
            self.subbuffer.action_mask.append(mask)

            next_subenv_obs = {
                'p_net_x': next_subenv_obs['p_net_x'],
                'p_net_edge': next_subenv_obs['p_net_edge'],
                'p_net_node': p_node_id,
                'hidden_state': hidden_state.squeeze(0).cpu().detach().numpy(),
                'encoder_outputs': encoder_outputs
            }

            if subenv_done:
                break

            subenv_obs = next_subenv_obs

        self.tracer.handle_data(self.subenv,None)

        p_net_obs_tensor = SubEnv.p_net_obs_to_tensor(subenv_obs,self.device)
        last_value = self.policy.evaluate(p_net_obs_tensor).squeeze(-1).detach().cpu()

        return self.subenv.subsolution, self.subbuffer, last_value
    
    def solve_embedding(self, event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        self.solution.resource['cpu'] = [self.vnfManager.vnfPoolDict[vnfId].vnf_cpu for vnfId in vnfRequstList]
        self.solution.resource['ram'] = [self.vnfManager.vnfPoolDict[vnfId].vnf_ram for vnfId in vnfRequstList]
        self.solution.resource['band'] = [self.vnfManager.vnfServicePoolDict[vnfRequstList[i],vnfRequstList[i+1]]['band'] 
                                          for i in range(len(vnfRequstList)-1)]

        subsolution, subbuffer, lastvalue = self.learn(event,self.solution)
        self.merge_experience(subsolution,subbuffer)

        if self.buffer.size() >= 128:
            self.update()

        if subsolution.result == True:
            for i,node in enumerate(self.sfcGraph.nodes):
                self.solution.map_node[node] = subsolution.selected_actions[i]
        else:
            for i,node in enumerate(self.sfcGraph.nodes):
                self.solution.map_node[node] = random.sample(range(len(self.substrateTopo.nodes)),1)[0]

        for v_link in self.sfcGraph.edges():
            map_path = nx.dijkstra_path(self.substrateTopo,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        # algorithm end ---------------------------------------------

        self.solution.current_description = self.check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.SET_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True
        
        self.record_solutions[self.event.serviceTopoId]=[self.solution]

        return self.solution
    
    def solve_migration(self, event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        self.solution.resource['cpu'] = [self.vnfManager.vnfPoolDict[vnfId].vnf_cpu for vnfId in vnfRequstList]
        self.solution.resource['ram'] = [self.vnfManager.vnfPoolDict[vnfId].vnf_ram for vnfId in vnfRequstList]
        self.solution.resource['band'] = [self.vnfManager.vnfServicePoolDict[vnfRequstList[i],vnfRequstList[i+1]]['band'] 
                                          for i in range(len(vnfRequstList)-1)]

        subsolution, subbuffer, lastvalue = self.learn(event,self.solution)
        self.merge_experience(subsolution,subbuffer)

        if self.buffer.size() >= 128:
            self.update()

        if subsolution.result == True:
            for i,node in enumerate(self.sfcGraph.nodes):
                self.solution.map_node[node] = subsolution.selected_actions[i]
        else:
            for i,node in enumerate(self.sfcGraph.nodes):
                self.solution.map_node[node] = random.sample(range(len(self.substrateTopo.nodes)),1)[0]

        for v_link in self.sfcGraph.edges():
            map_path = nx.dijkstra_path(self.substrateTopo,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        # algorithm end ---------------------------------------------

        self.solution.current_description = self.check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.CHANGE_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True
        
        self.record_solutions[self.event.serviceTopoId].append(self.solution)

        return self.solution

    def saveParam(self):
        self.tracer.save_model(**{'policy': self.policy.state_dict(),'optimizer': self.optimizer.state_dict()})

    def loadParam(self):
        policy_param, optimizer_param = self.tracer.load_model()
        if policy_param != None and optimizer_param != None:
            self.policy.load_state_dict(policy_param)
            self.optimizer.load_state_dict(optimizer_param)
        