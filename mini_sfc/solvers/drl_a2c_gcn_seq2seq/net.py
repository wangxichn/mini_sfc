#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   net.py
@Time    :   2024/03/20 20:56:11
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_scatter import scatter
from torch_geometric.nn import GCNConv, global_add_pool, global_max_pool, global_mean_pool
from torch_geometric.utils import to_dense_batch
import code

class ActorCritic(nn.Module):
    def __init__(self, p_net_num_nodes, p_net_feature_dim, v_net_feature_dim, embedding_dim=64):
        super(ActorCritic, self).__init__()
        self.encoder = Encoder(v_net_feature_dim, embedding_dim=embedding_dim)
        self.actor = Actor(p_net_num_nodes, p_net_feature_dim, v_net_feature_dim, embedding_dim)
        self.critic = Critic(p_net_num_nodes, p_net_feature_dim, v_net_feature_dim, embedding_dim)
        self._last_hidden_state = None

    def encode(self, obs):
        x = obs['v_net_x']
        outputs, hidden_state = self.encoder(x)
        self._last_hidden_state = hidden_state
        return outputs

    def act(self, obs):
        logits, outputs, hidden_state = self.actor(obs)
        self._last_hidden_state = hidden_state
        return logits

    def evaluate(self, obs):
        value = self.critic(obs)
        return value

    def get_last_rnn_state(self):
        return self._last_hidden_state

    def set_last_rnn_hidden(self, hidden_state):
        self._last_hidden_state = hidden_state


class Actor(nn.Module):
    def __init__(self, p_net_num_nodes, p_net_feature_dim, v_net_feature_dim, embedding_dim=64):
        super(Actor, self).__init__()
        self.decoder = Decoder(p_net_num_nodes, p_net_feature_dim, embedding_dim=embedding_dim)

    def forward(self, obs):
        """Return logits of actions"""
        logits, outputs, hidden_state = self.decoder(obs)
        return logits, outputs, hidden_state


class Critic(nn.Module):
    def __init__(self, p_net_num_nodes, p_net_feature_dim, v_net_feature_dim, embedding_dim=64):
        super(Critic, self).__init__()
        self.decoder = Decoder(p_net_num_nodes, p_net_feature_dim, embedding_dim=embedding_dim)

    def forward(self, obs):
        """Return logits of actions"""
        logits, outputs, hidden_state = self.decoder(obs)
        value = torch.mean(logits, dim=-1, keepdim=True)
        return value


class Encoder(nn.Module):
    def __init__(self, v_net_feature_dim, embedding_dim=64):
        super(Encoder, self).__init__()
        self.emb = nn.Linear(v_net_feature_dim, embedding_dim)
        self.gru = nn.GRU(embedding_dim, embedding_dim)

    def forward(self, x):
        """Encoder forward

        Args:
            x (FloatTensor): input 1 * v_net_node_num * v_net_feature_dim

        Returns:
            outputs (FloatTensor): v_net_node_num * 1 * embedding_dim
            hidden_state (FloatTensor): 1 * 1 * embedding_dim

        """
        x = x.permute(1, 0, 2)
        embeddings = F.relu(self.emb(x))
        outputs, hidden_state = self.gru(embeddings)

        return outputs, hidden_state
    

class Decoder(nn.Module):
    def __init__(self, p_net_num_nodes, feature_dim, embedding_dim=64):
        super(Decoder, self).__init__()
        self.emb = nn.Embedding(p_net_num_nodes + 1, embedding_dim)
        self.att = Attention(embedding_dim)
        self.gcn = GCNConvNet(feature_dim, embedding_dim, embedding_dim=embedding_dim, dropout_prob=0., return_batch=True)
        self.mlp = nn.Sequential(
            nn.Linear(embedding_dim, 1),
            nn.Flatten()
        )
        # self.out = nn.Sequential(
        #     GCNConvNet(embedding_dim, 1, embedding_dim=embedding_dim, dropout_prob=0., return_batch=True),
        #     nn.Flatten(),
        # )
        self.gru = nn.GRU(embedding_dim, embedding_dim)
        self._last_hidden_state = None

    def forward(self, obs:dict):
        batch_p_net = obs['p_net']
        hidden_state = obs['hidden_state']
        p_node_id = obs['p_net_node']
        hidden_state = hidden_state.permute(1, 0, 2)
        encoder_outputs = obs['encoder_outputs']
        mask = obs.get('mask',None)
        p_node_emb = self.emb(p_node_id).unsqueeze(0)
        context, attention = self.att(hidden_state, encoder_outputs, mask)
        outputs, hidden_state = self.gru(p_node_emb, hidden_state)
        p_node_embeddings = self.gcn(batch_p_net)
        p_node_embeddings = p_node_embeddings.reshape(batch_p_net.num_graphs, -1, p_node_embeddings.shape[-1])
        p_node_embeddings = p_node_embeddings + context
        logits = self.mlp(p_node_embeddings)
        return logits, outputs, hidden_state


class Attention(nn.Module):
    def __init__(self, hidden_dim):
        super().__init__()
        self.attn = nn.Linear(hidden_dim * 2, hidden_dim)
        self.v = nn.Linear(hidden_dim, 1, bias=False)

    def forward(self, hidden, encoder_outputs, mask=None):
        # hidden shape: (num_layers * num_directions, batch_size, hidden_dim)
        # encoder_outputs shape: (batch_size, seq_len, hidden_dim * num_directions)
        batch_size = encoder_outputs.size(0)
        seq_len = encoder_outputs.size(1)
        hidden = hidden.transpose(0, 1).repeat(1, seq_len, 1)  # shape: (batch_size, seq_len, hidden_dim)
        energy = torch.tanh(self.attn(torch.cat([hidden, encoder_outputs], dim=2)))  # shape: (batch_size, seq_len, hidden_dim)
        attn_weights = F.softmax(self.v(energy).squeeze(2), dim=1)  # shape: (batch_size, seq_len)
        if mask is not None:
            attn_weights = attn_weights.masked_fill(mask == 0, -1e10)
        context = torch.bmm(attn_weights.unsqueeze(1), encoder_outputs)  # shape: (batch_size, 1, hidden_dim * num_directions)
        return context, attn_weights
    

class GraphPooling(nn.Module):
    def __init__(self, aggr='sum', **kwargs):
        super(GraphPooling, self).__init__()
        if aggr in ['att', 'attention']:
            output_dim = kwargs.get('output_dim')
            self.pooling = GraphAttentionPooling(output_dim)
        elif aggr in ['add', 'sum']:
            self.pooling = global_add_pool
        elif aggr == 'max':
            self.pooling = global_max_pool
        elif aggr == 'mean':
            self.pooling = global_mean_pool
        else:
            return NotImplementedError

    def forward(self, x, batch):
        return self.pooling(x, batch)


class GCNConvNet(nn.Module):
    """Graph Convolutional Network to extract the feature of physical network."""
    def __init__(self, input_dim, output_dim, embedding_dim=128, num_layers=3, batch_norm=True, dropout_prob=1.0, return_batch=False, pooling=None, **kwargs):
        super(GCNConvNet, self).__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.num_layers = num_layers
        self.return_batch = return_batch
        self.pooling = pooling
        if self.pooling is not None:
            self.graph_pooling = GraphPooling(aggr=pooling, output_dim=output_dim)

        for layer_id in range(self.num_layers):
            if self.num_layers == 1:
                conv = GCNConv(input_dim, output_dim)
            elif layer_id == 0:
                conv = GCNConv(input_dim, embedding_dim)
            elif layer_id == num_layers - 1:
                conv = GCNConv(embedding_dim, output_dim)
            else:
                conv = GCNConv(embedding_dim, embedding_dim)
                
            norm_dim = output_dim if layer_id == num_layers - 1 else embedding_dim
            norm = nn.BatchNorm1d(norm_dim) if batch_norm else nn.Identity()
            dout = nn.Dropout(dropout_prob) if dropout_prob < 1. else nn.Identity()

            self.add_module('conv_{}'.format(layer_id), conv)
            self.add_module('norm_{}'.format(layer_id), norm)
            self.add_module('dout_{}'.format(layer_id), dout)

        self._init_parameters()

    def _init_parameters(self):
        for layer_id in range(self.num_layers):
            nn.init.orthogonal_(getattr(self, f'conv_{layer_id}').lin.weight)

    def forward(self, input):
        x, edge_index = input['x'], input['edge_index']

        for layer_id in range(self.num_layers):
            conv = getattr(self, 'conv_{}'.format(layer_id))
            norm = getattr(self, 'norm_{}'.format(layer_id))
            dout = getattr(self, 'dout_{}'.format(layer_id))
            x = conv(x, edge_index)
            if layer_id == self.num_layers - 1:
                x = dout(norm(x))
            else:
                x = F.leaky_relu(dout(norm(x)))
        if self.return_batch:
            x, mask = to_dense_batch(x, input.batch)
        if self.pooling is not None:
            x = self.graph_pooling(x, input.batch)
        return x
    

class GraphAttentionPooling(nn.Module):
    """Attention module to extract global feature of a graph."""
    def __init__(self, input_dim):
        super(GraphAttentionPooling, self).__init__()
        self.input_dim = input_dim
        self.weight = nn.Parameter(torch.Tensor(self.input_dim, self.input_dim))
        self._init_parameters()

    def _init_parameters(self):
        """Initializing weights."""
        nn.init.orthogonal_(self.weight)

    def forward(self, x, batch, size=None):
        """
        Making a forward propagation pass to create a graph level representation.

        Args:
            x (torch.Tensor): Result of the GNN.
            batch (torch.Tensor): Batch vector, which assigns each node to a specific example
            size (int, optional): Number of nodes in the graph. Defaults to None.

        Returns:
            representation: A graph level representation matrix.
        """
        size = batch[-1].item() + 1 if size is None else size
        mean = scatter(x, batch, dim=0, dim_size=size, reduce='mean')
        transformed_global = torch.tanh(torch.mm(mean, self.weight))

        coefs = torch.sigmoid((x * transformed_global[batch] * 10).sum(dim=1))
        weighted = coefs.unsqueeze(-1) * x

        return scatter(weighted, batch, dim=0, dim_size=size, reduce='add')

    def get_coefs(self, x):
        mean = x.mean(dim=0)
        transformed_global = torch.tanh(torch.matmul(mean, self.weight))

        return torch.sigmoid(torch.matmul(x, transformed_global))


def apply_mask_to_logit(logit, mask=None):
    """
    Apply a mask to a given logits tensor.

    Args:
        logit (tensor): input logits tensor
        mask (tensor, optional): input mask tensor. Defaults to None.

    Returns:
        masked_logit (tensor): the masked logits tensor
    """
    if mask is None:
        return logit
    # mask = torch.IntTensor(mask).to(logit.device).expand_as(logit)
    # masked_logit = logit + mask.log()
    if not isinstance(mask, torch.Tensor):
        mask = torch.BoolTensor(mask)
    
    # flag = ~torch.any(mask, dim=1, keepdim=True).repeat(1, mask.shape[-1])
    # mask = torch.where(flag, True, mask)
    
    mask = mask.bool().to(logit.device).reshape(logit.size())

    # A constant tensor used to mask values
    NEG_TENSER = torch.tensor(-1e8).float()
    mask_value_tensor = NEG_TENSER.type_as(logit).to(logit.device)
    masked_logit = torch.where(mask, logit, mask_value_tensor)
    return masked_logit


if __name__ == "__main__":
    device = torch.device('cpu')
    policy = ActorCritic(p_net_num_nodes=100, p_net_feature_dim=5, v_net_feature_dim=2, embedding_dim=64).to(device)

    code.interact(banner="",local=locals())
