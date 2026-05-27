import torch
import torch.nn as nn

class DummyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(10, 10)
        self.fc2 = nn.Linear(10, 2)

model = DummyModel()
torch.save({"model": model.state_dict()}, "checkpoint.pt")
print("Saved checkpoint.pt")
