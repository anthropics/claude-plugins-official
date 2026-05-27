#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════╗
# ║  ARKHE PHYSICS PRIORS — Substrato 890.2                         ║
# ║  Módulo de priors físicos: gravidade, colisão, oclusão          ║
# ╚══════════════════════════════════════════════════════════════════╝

"""
Módulo de Physics Priors para o World Model.

Este módulo implementa priors físicos indutivos que guiam o modelo
a aprender leis da física de forma mais eficiente:
  - Gravidade: objetos caem (y decresce)
  - Colisão: objetos não penetram
  - Oclusão: objetos atrás de barreiras não são visíveis
  - Conservação: momentum, energia (aproximado)
  - Continuidade: trajetórias são suaves

Arquitetura:
  Embedding LLM (512) → MLP Physics Priors → Physics Embedding (256)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple

class PhysicsPriorsModule(nn.Module):
    """
    Módulo de priors físicos indutivos.

    Projeta embeddings de linguagem para um espaço físico-estruturado
    onde priors como gravidade, colisão e oclusão são codificados
    como regularizações e biases arquiteturais.

    Args:
        d_model: dimensão do embedding de linguagem (512)
        state_dim: dimensão do estado físico (256)
        hidden_dim: dimensão das camadas ocultas
        n_priors: número de priors físicos (5)
    """

    def __init__(
        self,
        d_model: int = 512,
        state_dim: int = 256,
        hidden_dim: int = 256,
        n_priors: int = 5,
    ):
        super().__init__()
        self.d_model = d_model
        self.state_dim = state_dim
        self.n_priors = n_priors

        # Priors codificados como projeções especializadas
        self.prior_projections = nn.ModuleDict({
            "gravity": nn.Sequential(
                nn.Linear(d_model, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, state_dim // n_priors),
            ),
            "collision": nn.Sequential(
                nn.Linear(d_model, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, state_dim // n_priors),
            ),
            "occlusion": nn.Sequential(
                nn.Linear(d_model, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, state_dim // n_priors),
            ),
            "conservation": nn.Sequential(
                nn.Linear(d_model, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, state_dim // n_priors),
            ),
            "continuity": nn.Sequential(
                nn.Linear(d_model, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, state_dim // n_priors),
            ),
        })

        # Fusão adaptativa dos priors
        self.prior_gate = nn.Sequential(
            nn.Linear(d_model, n_priors),
            nn.Softmax(dim=-1),
        )

        # Projeção final
        # Note: state_dim // n_priors * n_priors is used because 256 // 5 * 5 = 255 != 256
        self.output_proj = nn.Sequential(
            nn.Linear((state_dim // n_priors) * n_priors, state_dim),
            nn.LayerNorm(state_dim),
            nn.ReLU(),
        )

        print(f"[890.2] PhysicsPriorsModule: {d_model}→{state_dim}, {n_priors} priors")

    def forward(self, text_embedding: torch.Tensor) -> torch.Tensor:
        """
        Projeta embedding de linguagem para espaço físico.

        Args:
            text_embedding: [batch, d_model] ou [d_model]

        Returns:
            physics_embedding: [batch, state_dim] ou [state_dim]
        """
        if text_embedding.dim() == 1:
            text_embedding = text_embedding.unsqueeze(0)
            squeeze = True
        else:
            squeeze = False

        batch_size = text_embedding.size(0)

        # Computar cada prior
        prior_outputs = []
        for name, proj in self.prior_projections.items():
            prior_emb = proj(text_embedding)  # [batch, state_dim//n_priors]
            prior_outputs.append(prior_emb)

        # Concatenar priors
        prior_stack = torch.cat(prior_outputs, dim=-1)  # [batch, state_dim]

        # Gate adaptativo: quais priors são relevantes para esta entrada?
        gate_weights = self.prior_gate(text_embedding)  # [batch, n_priors]

        # Aplicar gate por blocos
        prior_dim = self.state_dim // self.n_priors
        gated_priors = []
        for i in range(self.n_priors):
            w = gate_weights[:, i:i+1]  # [batch, 1]
            block = prior_stack[:, i*prior_dim:(i+1)*prior_dim]
            gated_priors.append(w * block)

        gated_output = torch.cat(gated_priors, dim=-1)

        # Projeção final
        physics_embedding = self.output_proj(gated_output)

        if squeeze:
            physics_embedding = physics_embedding.squeeze(0)

        return physics_embedding

    def get_prior_importance(self, text_embedding: torch.Tensor) -> dict:
        """
        Retorna importância de cada prior para uma dada entrada.

        Útil para interpretabilidade: "Este texto ativa priors de gravidade."
        """
        with torch.no_grad():
            gate_weights = self.prior_gate(text_embedding)
            if gate_weights.dim() == 2:
                gate_weights = gate_weights.squeeze(0)

        prior_names = list(self.prior_projections.keys())
        return {name: float(gate_weights[i]) for i, name in enumerate(prior_names)}

class GravityPrior(nn.Module):
    """
    Prior específico de gravidade.

    Codifica o bias de que objetos tendem a cair (aceleração -g em y).
    Usado como regularização durante o treinamento.
    """

    def __init__(self, g: float = 9.81):
        super().__init__()
        self.g = g

    def forward(self, positions: torch.Tensor, dt: float = 0.02) -> torch.Tensor:
        """
        Aplica aceleração gravitacional a posições.

        Args:
            positions: [batch, 3] — (x, y, z)
            dt: passo de tempo

        Returns:
            new_positions: [batch, 3] — posições após dt sob gravidade
        """
        new_pos = positions.clone()
        new_pos[:, 1] -= 0.5 * self.g * dt ** 2  # Δy = -½gt²
        return new_pos

    def loss(self, pred_positions: torch.Tensor, true_positions: torch.Tensor) -> torch.Tensor:
        """
        Loss de consistência gravitacional.
        Penaliza predições que ignoram gravidade.
        """
        # Verificar se y decresceu apropriadamente
        pred_dy = pred_positions[:, 1] - true_positions[:, 1]
        expected_dy = -0.5 * self.g * (0.02 ** 2)

        return F.mse_loss(pred_dy, torch.full_like(pred_dy, expected_dy))

class CollisionPrior(nn.Module):
    """
    Prior de colisão: objetos não penetram.

    Codifica o bias de que volumes ocupados não se sobrepõem.
    """

    def __init__(self, min_distance: float = 0.1):
        super().__init__()
        self.min_distance = min_distance

    def loss(self, positions: torch.Tensor, radii: torch.Tensor) -> torch.Tensor:
        """
        Penaliza penetração entre objetos.

        Args:
            positions: [batch, n_objects, 3]
            radii: [batch, n_objects]
        """
        batch_size, n_objects, _ = positions.shape

        # Calcular distâncias pairwise
        # [batch, n, n, 3]
        diff = positions.unsqueeze(2) - positions.unsqueeze(1)
        distances = torch.norm(diff, dim=-1)  # [batch, n, n]

        # Soma de raios
        sum_radii = radii.unsqueeze(1) + radii.unsqueeze(2)  # [batch, n, n]

        # Penetração: distância < soma_radii
        penetration = torch.relu(sum_radii - distances + self.min_distance)

        # Penalizar apenas triângulo inferior (evitar duplo count)
        mask = torch.tril(torch.ones(n_objects, n_objects), diagonal=-1).bool()
        penetration = penetration[:, mask]

        return penetration.sum() / (batch_size * max(n_objects * (n_objects - 1) / 2, 1))
