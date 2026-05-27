import torch
import numpy as np

class SimulationConfig:
    pass

class ArkheBraxSimulator:
    def __init__(self, scene):
        pass
    def reset(self, seed=None):
        return {"x": np.zeros(3), "qd": np.zeros(6)}
    def step(self, state, action):
        return {"x": np.zeros(3), "qd": np.zeros(6)}
    def get_world_embedding(self, state):
        return torch.zeros(256)
    def get_trajectory_embedding(self, window=5):
        return torch.zeros(256)
