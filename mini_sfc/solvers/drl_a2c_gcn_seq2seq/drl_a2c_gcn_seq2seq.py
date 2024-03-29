#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   drl_a2c_gcn_seq2seq.py
@Time    :   2024/03/20 18:54:57
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from solvers import SOLVER_REGISTRAR, Solver, SolverMode
from solvers import Solution, SOLUTION_TYPE, SolutionGroup
from data import SubstrateNetwork
from base import Event,EventType
import networkx as nx
import code
import random
import copy 
import time
import numpy as np
from .net import ActorCritic, apply_mask_to_logit
from .buffer import RolloutBuffer
from .subenv import SubEnv
from .tracer import Tracer
from .subsolution import SubSolution
import torch
from torch_geometric.data import Data, Batch
import torch.nn.functional as F
from torch.distributions import Categorical

@SOLVER_REGISTRAR.regist(solver_name='drl_a2c_gcn_seq2seq',
                         solver_mode=SolverMode.CENTRALIZED)
class DrlA2cGcnSeq2seq(Solver,object):
    __instance = None
    def __new__(cls,*args,**kwargs):
        if not cls. __instance:
            cls.__instance = super().__new__(cls,*args,**kwargs)
        return cls.__instance

    def __init__(self) -> None:
        super().__init__()


    def initialize_centralized(self,**kwargs):
        MAX_CPU_Y = 20+1
        MAX_RAM_X = 20+1
        MIN_DEVISE_LATENCY = 0.01
        MAX_DEVISE_LATENCY = MIN_DEVISE_LATENCY + MIN_DEVISE_LATENCY * (MAX_CPU_Y-1+MAX_RAM_X-1)
        self.DEVISE_LATENCY_MAT = np.zeros((MAX_CPU_Y,MAX_RAM_X))
        for i in range(MAX_CPU_Y):
            for j in range(MAX_RAM_X):
                self.DEVISE_LATENCY_MAT[i,j] = MAX_DEVISE_LATENCY-(i+j)*MIN_DEVISE_LATENCY

        self.use_cuda = False
        if self.use_cuda and torch.cuda.is_available():
            self.device = torch.device('cuda:0')
        else:
            self.device = torch.device('cpu')

        self.buffer = RolloutBuffer()

        p_net:SubstrateNetwork = kwargs.get("substrate_network",None)

        self.policy = ActorCritic(p_net_num_nodes=p_net.num_nodes, 
                                  p_net_feature_dim=10, v_net_feature_dim=5, 
                                  embedding_dim=64).to(self.device)
        
        self.optimizer = torch.optim.Adam([
                {'params': self.policy.actor.parameters(), 'lr': 0.005},
                {'params': self.policy.critic.parameters(), 'lr': 0.001},
            ],
        )

        self.tracer = Tracer()

        policy_param, optimizer_param = self.tracer.load_model()
        if policy_param != None and optimizer_param != None:
            self.policy.load_state_dict(policy_param)
            self.optimizer.load_state_dict(optimizer_param)

    
    def ending_centralized(self):
        self.tracer.save_model(**{'policy': self.policy.state_dict(),'optimizer': self.optimizer.state_dict()})


    def initialize_distributed(self,event: Event) -> None:
        pass

    def ending_distributed(self):
        pass


    def __v_net_obs_to_tensor(self, obs:dict, device) -> dict:
        """__v_net_obs_to_tensor

        Args:
            obs (dict): _description_
            device (_type_): _description_

        Returns:
            dict: {'v_net_x': obs_v_net_x}
        """
        if isinstance(obs, dict):
            v_net_x = obs['v_net_x']
            obs_v_net_x = torch.FloatTensor(v_net_x).unsqueeze(dim=0).to(device)
            return {'v_net_x': obs_v_net_x}
        elif isinstance(obs, list):
            obs_batch = obs
            v_net_x_list = []
            for observation in obs:
                v_net_x = obs['v_net_x']
                v_net_x_list.append(v_net_x)
            obs_v_net_x = torch.FloatTensor(np.array(v_net_x_list)).to(device)
            return {'v_net_x': obs_v_net_x}
        else:
            raise Exception(f"Unrecognized type of observation {type(obs)}")
    
    def __p_net_obs_to_tensor(self, obs:dict, device) -> dict:
        """__p_net_obs_to_tensor

        Args:
            obs (dict): _description_
            device (_type_): _description_

        Returns:
            dict: { 'p_net': p_net_obs, 
                    'p_net_node': p_net_node, 
                    'hidden_state': hidden_state, 
                    'encoder_outputs': encoder_outputs}
        """
        if isinstance(obs, dict):
            p_net_x = torch.tensor(obs['p_net_x'])
            p_net_edge = torch.tensor(obs['p_net_edge']).long()
            p_net_edge_attr = None
            # Data object containing node and edge information in Pytorch Geometric format.
            data = Data(x=p_net_x, edge_index=p_net_edge, edge_attr=p_net_edge_attr)
            p_net_obs = Batch.from_data_list([data]).to(device)
            p_net_node = torch.LongTensor([obs['p_net_node']]).to(device)
            hidden_state = torch.FloatTensor(obs['hidden_state']).unsqueeze(dim=0).to(device)
            encoder_outputs = torch.FloatTensor(obs['encoder_outputs']).unsqueeze(dim=0).to(device)

            return {'p_net': p_net_obs, 'p_net_node': p_net_node, 
                    'hidden_state': hidden_state, 'encoder_outputs': encoder_outputs}
        elif isinstance(obs, list):
            obs_batch = obs
            p_net_data_list, p_net_node_list, hidden_state_list, encoder_outputs_list = [], [], [], []
            for observation in obs_batch:
                p_net_x = torch.tensor(observation['p_net_x'])
                p_net_edge = torch.tensor(observation['p_net_edge']).long()
                p_net_edge_attr = None
                # Data object containing node and edge information in Pytorch Geometric format.
                p_net_data = Data(x=p_net_x, edge_index=p_net_edge, edge_attr=p_net_edge_attr)
                p_net_node = observation['p_net_node']
                hidden_state = observation['hidden_state']
                encoder_outputs = observation['encoder_outputs']
                p_net_data_list.append(p_net_data)
                p_net_node_list.append(p_net_node)
                hidden_state_list.append(hidden_state)
                encoder_outputs_list.append(encoder_outputs)
            obs_p_net_node = torch.LongTensor(np.array(p_net_node_list)).to(device)
            obs_hidden_state = torch.FloatTensor(np.array(hidden_state_list)).to(device)
            obs_p_net = Batch.from_data_list(p_net_data_list).to(device)
            # Pad sequences with zeros and get the mask of padded elements
            sequences = encoder_outputs_list
            max_length = max([seq.shape[0] for seq in sequences])
            padded_sequences = np.zeros((len(sequences), max_length, sequences[0].shape[1]))
            mask = np.zeros((len(sequences), max_length), dtype=np.bool_)
            for i, seq in enumerate(sequences):
                seq_len = seq.shape[0]
                padded_sequences[i, :seq_len, :] = seq
                mask[i, :seq_len] = 1
            obs_encoder_outputs = torch.FloatTensor(np.array(padded_sequences)).to(device)
            obs_mask = torch.FloatTensor(mask).to(device)

            return {'p_net': obs_p_net, 'p_net_node': obs_p_net_node, 
                    'hidden_state': obs_hidden_state, 'encoder_outputs': obs_encoder_outputs}
        else:
            raise ValueError('obs type error')

    def __select_action(self, observation, mask=None, sample=True):
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

    def __estimate_obs(self, observation):
        return self.policy.evaluate(observation).squeeze(-1).detach().cpu()
    
    def __merge_experience(self,subsolution:SubSolution,subbuffer:RolloutBuffer):
        if subsolution.result == True:
            subbuffer.compute_mc_returns(gamma=0.95)
            self.buffer.merge(subbuffer)
        else:
            pass
    
    def __update(self):
        observations = self.__p_net_obs_to_tensor(self.buffer.observations, self.device)
        actions = torch.LongTensor(np.concatenate(self.buffer.actions, axis=0)).to(self.device)
        returns = torch.FloatTensor(self.buffer.returns).to(self.device)
        if len(self.buffer.action_mask) != 0:
            masks = torch.IntTensor(np.concatenate(self.buffer.action_mask, axis=0)).to(self.device)
        else:
            masks = None

        values, action_logprobs, dist_entropy, other = self.__evaluate_actions(observations, actions, masks=masks, return_others=True)

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
    
    def __evaluate_actions(self, old_observations, old_actions, masks=None, return_others=False):
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


    def __learn(self,event: Event):
        self.subbuffer = RolloutBuffer()
    
        self.subenv = SubEnv(copy.deepcopy(event))
        subenv_obs = self.subenv.get_observation()
        subenv_done = False

        v_net_obs_tensor = self.__v_net_obs_to_tensor(subenv_obs,self.device)
        encoder_outputs = self.policy.encode(v_net_obs_tensor)
        # remove dim 1 & to CPU & detach the tensor from the current calculation graph & change to numpy
        encoder_outputs = encoder_outputs.squeeze(1).cpu().detach().numpy()

        subenv_obs = {
            'p_net_x': subenv_obs['p_net_x'],
            'p_net_edge': subenv_obs['p_net_edge'],
            'p_net_node': self.subenv.p_net.num_nodes,
            'hidden_state': self.policy.get_last_rnn_state().squeeze(0).cpu().detach().numpy(),
            'encoder_outputs': encoder_outputs
        }

        while not subenv_done:
            hidden_state = self.policy.get_last_rnn_state()
            mask = np.expand_dims(self.subenv.get_action_mask(), axis=0)
            p_net_obs_tensor = self.__p_net_obs_to_tensor(subenv_obs,self.device)
            action, action_logprob = self.__select_action(p_net_obs_tensor, mask=mask, sample=True)
            value = self.__estimate_obs(p_net_obs_tensor) if hasattr(self.policy, 'evaluate') else None

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

        p_net_obs_tensor = self.__p_net_obs_to_tensor(subenv_obs,self.device)
        last_value = self.__estimate_obs(p_net_obs_tensor) if hasattr(self.policy, 'evaluate') else None

        return self.subenv.subsolution, self.subbuffer, last_value
        
    def solve_embedding(self,event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        self.service_chain = event.sfc
        self.substrate_network = event.current_substrate

        self.solution.current_time = event.time
        self.solution.current_service_chain = copy.deepcopy(event.sfc)
        self.solution.current_substrate_net = copy.deepcopy(event.current_substrate)

        solve_start_time = time.time()

        # algorithm begin ---------------------------------------------
        subsolution, subbuffer, lastvalue = self.__learn(event)
        self.__merge_experience(subsolution,subbuffer)

        if self.buffer.size() >= 128:
            self.__update()

        if subsolution.result == True:
            for i,node in enumerate(self.service_chain.nodes):
                self.solution.map_node_last[node] = None
                self.solution.map_node[node] = subsolution.selected_actions[i]
        else:
            for i,node in enumerate(self.service_chain.nodes):
                self.solution.map_node_last[node] = None
                self.solution.map_node[node] = random.sample(range(self.substrate_network.num_nodes),1)[0]

            
        for v_link in self.service_chain.edges():
            map_path = nx.dijkstra_path(self.substrate_network,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            
            self.solution.map_link_last[v_link] = []
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        
        # algorithm end ---------------------------------------------
        
        self.solution.current_description = self.__check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.SET_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True

        self.__perform_measure(event)
        self.solution.cost_real_time = time.time()-solve_start_time

        return self.solution

    def solve_migration(self,event: Event,solution_last: Solution) -> Solution:
        self.event = event
        self.solution = Solution()
        self.service_chain = event.sfc
        self.substrate_network = event.current_substrate

        self.solution.current_time = event.time
        self.solution.current_service_chain = copy.deepcopy(event.sfc)
        self.solution.current_substrate_net = copy.deepcopy(event.current_substrate)

        solve_start_time = time.time()

        self.solution.map_node_last = copy.deepcopy(solution_last.map_node) # Save previous data
        self.solution.map_link_last = copy.deepcopy(solution_last.map_link) # Save previous data

        # algorithm begin ---------------------------------------------
        
        subsolution, subbuffer, lastvalue = self.__learn(event)

        self.__merge_experience(subsolution,subbuffer)

        if self.buffer.size() >= 128:
            self.__update()

        if subsolution.result == True:
            for i,node in enumerate(self.service_chain.nodes):
                self.solution.map_node[node] = subsolution.selected_actions[i]
        else:
            for i,node in enumerate(self.service_chain.nodes):
                self.solution.map_node[node] = random.sample(range(self.substrate_network.num_nodes),1)[0]

        for v_link in self.service_chain.edges():
            map_path = nx.dijkstra_path(self.substrate_network,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        
        # algorithm end ---------------------------------------------

        self.solution.current_description = self.__check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.CHANGE_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True

        self.__perform_measure(event)
        self.solution.cost_real_time = time.time()-solve_start_time

        return self.solution

    def solve_ending(self,event: Event,solution_last: Solution) -> Solution:
        self.event = event
        self.solution = Solution()
        self.service_chain = event.sfc
        self.substrate_network = event.current_substrate

        self.solution.current_time = event.time
        self.solution.current_service_chain = copy.deepcopy(event.sfc)
        self.solution.current_substrate_net = copy.deepcopy(event.current_substrate)

        solve_start_time = time.time()

        self.solution.map_node_last = copy.deepcopy(solution_last.map_node) # Save previous data but not use
        self.solution.map_link_last = copy.deepcopy(solution_last.map_link) # Save previous data but not use

        # algorithm begin ---------------------------------------------
        
        self.solution.map_node = self.solution.map_node_last
        self.solution.map_link = self.solution.map_link_last

        # algorithm end ----------------------------------------------

        self.solution.current_description = SOLUTION_TYPE.END_SUCCESS
        self.solution.current_result = True

        self.__perform_measure(event)

        self.solution.cost_real_time =  time.time()-solve_start_time

        return self.solution
    
    def __check_constraints(self, event: Event) -> SOLUTION_TYPE:
        # Node Resource Constraint Check
        remain_cpu_of_nodes = self.substrate_network.get_all_nodes_attrs_values("cpu_setting","remain_setting")
        remain_ram_of_nodes = self.substrate_network.get_all_nodes_attrs_values("ram_setting","remain_setting")
        remain_disk_of_nodes = self.substrate_network.get_all_nodes_attrs_values("disk_setting","remain_setting")
        remain_eng_of_nodes = self.substrate_network.get_all_nodes_attrs_values("energy_setting","remain_setting")

        for sfc_node, phy_node in self.solution.map_node.items():     
            request_cpu_of_node = self.service_chain.get_node_attrs_value(sfc_node,"cpu_setting")
            request_ram_of_node = self.service_chain.get_node_attrs_value(sfc_node,"ram_setting")
            request_disk_of_node = self.service_chain.get_node_attrs_value(sfc_node,"disk_setting")
            request_eng_of_node = request_cpu_of_node * (self.service_chain.endtime - self.solution.current_time)
            
            remain_cpu_of_nodes[phy_node] -= request_cpu_of_node
            if remain_cpu_of_nodes[phy_node] < 0:
                if event.type == EventType.SFC_ARRIVE:
                    return SOLUTION_TYPE.SET_NODE_FAILED_FOR_CPU
                elif event.type == EventType.TOPO_CHANGE:
                    return SOLUTION_TYPE.CHANGE_NODE_FAILED_FOR_CPU
            
            remain_ram_of_nodes[phy_node] -= request_ram_of_node
            if remain_ram_of_nodes[phy_node] < 0:
                if event.type == EventType.SFC_ARRIVE:
                    return SOLUTION_TYPE.SET_NODE_FAILED_FOR_RAM
                elif event.type == EventType.TOPO_CHANGE:
                    return SOLUTION_TYPE.CHANGE_NODE_FAILED_FOR_RAM
            
            remain_disk_of_nodes[phy_node] -= request_disk_of_node
            if remain_disk_of_nodes[phy_node] < 0:
                if event.type == EventType.SFC_ARRIVE:
                    return SOLUTION_TYPE.SET_NODE_FAILED_FOR_DISK
                elif event.type == EventType.TOPO_CHANGE:
                    return SOLUTION_TYPE.CHANGE_NODE_FAILED_FOR_DISK
            
            remain_eng_of_nodes[phy_node] -= request_eng_of_node
            if remain_eng_of_nodes[phy_node] < 0:
                if event.type == EventType.SFC_ARRIVE:
                    return SOLUTION_TYPE.SET_NODE_FAILED_FOR_ENG
                elif event.type == EventType.TOPO_CHANGE:
                    return SOLUTION_TYPE.CHANGE_NODE_FAILED_FOR_ENG
            
        # Link Resource Constraint Check
        remain_band_of_links = self.substrate_network.get_all_links_attrs_values("band_setting","remain_setting")
        # code.interact(banner="",local=locals())
        CHECK_FLAG = True
        for sfc_link, phy_links in self.solution.map_link.items():
            if CHECK_FLAG == False: break
            request_band_of_link = self.service_chain.get_link_attrs_value(sfc_link,"band_setting")
            for phy_link in phy_links:
                remain_band_of_links[phy_link] -= request_band_of_link
                if remain_band_of_links[phy_link] < 0:
                    CHECK_FLAG = False
                    break
        if CHECK_FLAG == False:
            if event.type == EventType.SFC_ARRIVE:
                return SOLUTION_TYPE.SET_LINK_FAILED
            elif event.type == EventType.TOPO_CHANGE:
                return SOLUTION_TYPE.CHANGE_LINK_FAILED
        
        # Qos Constraint Check
        if self.__get_latency_running() > event.sfc.qos_latency:
            if event.type == EventType.SFC_ARRIVE:
                return SOLUTION_TYPE.SET_LATENCY_FAILED
            elif event.type == EventType.TOPO_CHANGE:
                return SOLUTION_TYPE.CHANGE_LATENCY_FAILED
        
        # All check passed
        if event.type == EventType.SFC_ARRIVE:
            return SOLUTION_TYPE.SET_SUCCESS
        elif event.type == EventType.TOPO_CHANGE:
            return SOLUTION_TYPE.CHANGE_SUCCESS
        
    def __perform_measure(self,event: Event):

        perform_all_use_cpu_resource = sum(self.service_chain.get_all_nodes_attrs_values("cpu_setting"))
        perform_all_use_ram_resource = sum(self.service_chain.get_all_nodes_attrs_values("ram_setting"))
        perform_all_use_disk_resource = sum(self.service_chain.get_all_nodes_attrs_values("disk_setting"))
        perform_all_use_energy_resource = sum(self.service_chain.get_all_nodes_attrs_values("cpu_setting"))

        perform_all_use_link_resource = sum(self.service_chain.get_all_links_attrs_values("band_setting").values())/2
            # for sfd_link, phy_links in self.solution.map_link.items():
            #     perform_all_use_link_resource += self.service_chain.get_link_attrs_value(sfd_link,"band_setting") * len(phy_links)

        perform_all_phy_cpu_resource = sum(self.substrate_network.get_all_nodes_attrs_values("cpu_setting","max_setting"))
        perform_all_phy_ram_resource = sum(self.substrate_network.get_all_nodes_attrs_values("ram_setting","max_setting"))
        perform_all_phy_disk_resource = sum(self.substrate_network.get_all_nodes_attrs_values("disk_setting","max_setting"))
        perform_all_phy_energy_resource = sum(self.substrate_network.get_all_nodes_attrs_values("cpu_setting","max_setting"))
        perform_all_phy_link_resource = sum(self.substrate_network.get_all_links_attrs_values("band_setting","max_setting").values())/2

        
        self.solution.perform_latency_run = self.__get_latency_running()
        self.solution.perform_latency_map = self.__get_latency_remap()
        self.solution.perform_latency_route = self.__get_latency_reroute()
        self.solution.perform_latency = self.solution.perform_latency_run + self.solution.perform_latency_map + self.solution.perform_latency_route

        self.solution.perform_revenue_unit = perform_all_use_cpu_resource * self.substrate_network.get_node_attrs_price("cpu_setting") + \
                                             perform_all_use_ram_resource * self.substrate_network.get_node_attrs_price("ram_setting") + \
                                             perform_all_use_disk_resource * self.substrate_network.get_node_attrs_price("disk_setting") + \
                                             perform_all_use_energy_resource * self.substrate_network.get_node_attrs_price("energy_setting") + \
                                             perform_all_use_link_resource * self.substrate_network.get_link_attrs_price("band_setting")

        self.solution.cost_node_resource = [perform_all_use_cpu_resource, perform_all_use_ram_resource, 
                                            perform_all_use_disk_resource, perform_all_use_energy_resource]
        self.solution.cost_node_resource_percentage = [perform_all_use_cpu_resource/perform_all_phy_cpu_resource, 
                                                       perform_all_use_ram_resource/perform_all_phy_ram_resource, 
                                                       perform_all_use_disk_resource/perform_all_phy_disk_resource, 
                                                       perform_all_use_energy_resource/perform_all_phy_energy_resource]
        self.solution.cost_link_resource = [perform_all_use_link_resource]
        self.solution.cost_link_resource_percentage = [perform_all_use_link_resource/perform_all_phy_link_resource]

    def __get_latency_running(self) -> float:
        latency_list = []
        for phy_node in self.solution.map_node.values():
            latency_list.append(self.substrate_network.get_node_latency_from_mat(phy_node,self.DEVISE_LATENCY_MAT))

        return max(latency_list)

    def __get_latency_remap(self) -> float:
        latency_list = []
        for vnf_node in self.solution.map_node.keys():
            if self.solution.map_node[vnf_node] != self.solution.map_node_last[vnf_node]:
                if vnf_node == 0:
                    latency_list.append(0)
                else:
                    latency_list.append(self.service_chain.get_node_attrs_value(vnf_node,"ram_setting") / self.service_chain.get_link_attrs_value((vnf_node-1,vnf_node),"band_setting"))
        return sum(latency_list)

    def __get_latency_reroute(self) -> float:
        REROUTE_TIME_UNIT = 0.01
        latency_list = []
        for vnf_link in self.solution.map_link.keys():
            vnf_link_diff = set(self.solution.map_link[vnf_link]) ^ set(self.solution.map_link_last[vnf_link])
            latency_list.append(len(vnf_link_diff)*REROUTE_TIME_UNIT)
        return sum(latency_list)
    
    @staticmethod
    def get_revenue(solution_group:SolutionGroup):
        revenue = 0
        time_list = [solution.current_time for solution in solution_group]
        for i in range(1,len(time_list),1):
            calculate_flag = solution_group[i-1].perform_latency < solution_group[i-1].current_service_chain.qos_latency
            calculate_time = time_list[i-1]+solution_group[i-1].perform_latency
            if calculate_time > time_list[i]: calculate_time = time_list[i]
            revenue = revenue + \
                      solution_group[i-1].perform_revenue_unit * (calculate_time-time_list[i-1]) * int(calculate_flag) + \
                      solution_group[i-1].perform_revenue_unit * (time_list[i]-calculate_time)
        return revenue
