import torch as th
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import DenseSAGEConv, dense_diff_pool, DenseGATConv
import numpy as np

class Critic(nn.Module):
    def __init__(self, n_agent, dim_observation, dim_action):
        super(Critic, self).__init__()
        self.n_agent = n_agent
        self.dim_observation = dim_observation
        self.dim_action = dim_action
        obs_dim = dim_observation * n_agent
        act_dim = self.dim_action * n_agent

        self.FC0 = nn.Linear(obs_dim, 4096)
        self.FC1 = nn.Linear(4096+act_dim, 2048)
        self.FC2 = nn.Linear(2048, 1024)
        self.FC3 = nn.Linear(1024, 512)
        self.FC4 = nn.Linear(512, 300)
        self.FC5 = nn.Linear(300, 1)

    # obs: batch_size * obs_dim
    def forward(self, obs, acts):
        # flatten obs
        obs = obs.view(-1, self.n_agent * self.dim_observation)
        result = F.relu(self.FC0(obs))
        combined = th.cat([result, acts], 1)
        result = F.relu(self.FC1(combined))
        result = F.relu(self.FC2(result))
        result = F.relu(self.FC3(result))

        return self.FC5(F.relu(self.FC4(result)))


class Actor(nn.Module):
    def __init__(self, dim_observation, dim_action):
        super(Actor, self).__init__()
        self.FC0 = nn.Linear(dim_observation, 2048)
        self.FC1 = nn.Linear(2048, 1024)
        self.FC2 = nn.Linear(1024, 512)
        self.FC3 = nn.Linear(512, 128)
        self.FC4 = nn.Linear(128, dim_action)

    # action output between -2 and 2
    def forward(self, obs):
        result = F.relu(self.FC0(obs))
        result = F.relu(self.FC1(result))
        result = F.relu(self.FC2(result))
        result = F.relu(self.FC3(result))
        result = F.tanh(self.FC4(result))
        return result

class PerceptGNN(nn.Module):
    def __init__(self, observation_shape):
        super(PerceptGNN, self).__init__()
        # self.gnn0 = DenseSAGEConv(observation_shape[-1], 512, normalize=True)
        self.gnn1 = DenseGATConv(observation_shape[-1], 32, heads=8, dropout=0)
        self.gnn2 = DenseGATConv(32*8, 32, heads=8, dropout=0)
        self.gnn3 = DenseGATConv(32*8, 16, heads=8, dropout=0)
        self.gnn4 = DenseGATConv(16*8, 16, heads=8, dropout=0)

        self.out_size = 16*8 * np.prod(observation_shape[:-1])
    # action output between -2 and 2
    def forward(self, x, adj, mask = None):
        # x = self.gnn0(x, adj, mask)
        x = self.gnn1(x, adj, mask)
        x = self.gnn2(x, adj)
        x = F.elu(x) # exponential linear unit
        x = self.gnn3(x, adj)
        x = self.gnn4(x, adj)
        x = F.elu(x) # exponential linear unit
        return x

# TODO: Gcritic and Gactor -- 다른 것보다 graph를 추가해야하는데 몇가지
#  argument들을 넣어서 해야함. args: hidden_dim size 가 필요하고, grid로 하는지..
class GCritic(nn.Module):
    def __init__(self, n_agent, dim_observation, dim_action):
        super(GCritic, self).__init__()
        self.n_agent = n_agent
        self.dim_observation = dim_observation
        self.dim_action = dim_action
        obs_dim = dim_observation
        act_dim = self.dim_action * n_agent

        self.FC1 = nn.Linear(obs_dim, 512)
        self.FC2 = nn.Linear(512+act_dim, 256)
        self.FC3 = nn.Linear(256, 128)
        self.FC4 = nn.Linear(128, 1)

    # obs: batch_size * obs_dim
    def forward(self, obs, acts):
        # flatten obs
        obs = obs.view(-1, self.dim_observation)
        result = F.relu(self.FC1(obs))
        combined = th.cat([result, acts], 1)
        result = F.relu(self.FC2(combined))
        return self.FC4(F.relu(self.FC3(result)))

class GActor(nn.Module):
    def __init__(self, dim_observation, dim_action):
        super(GActor, self).__init__()
        self.dim_observation = dim_observation
        self.FC1 = nn.Linear(dim_observation, 256)
        self.FC2 = nn.Linear(256, dim_action)

    # action output between -2 and 2
    def forward(self, obs):
        obs = obs.view(-1, self.dim_observation)
        result = F.relu(self.FC1(obs))
        result = F.relu(self.FC2(result))
        return result


class ActorMAAC(nn.Module):
    def __init__(self, dim_observation, dim_action):
        super(ActorMAAC, self).__init__()
        self.dim_observation = dim_observation
        self.FC1 = nn.Linear(dim_observation, 500)
        self.FC2 = nn.Linear(500, 128)
        self.FC3 = nn.Linear(128, dim_action)

    # action output between -2 and 2
    def forward(self, obs):
        # flatten obs
        obs = obs.view(-1, self.dim_observation)
        result = F.relu(self.FC1(obs))
        result = F.relu(self.FC2(result))
        result = F.softmax(self.FC3(result))
        return result
