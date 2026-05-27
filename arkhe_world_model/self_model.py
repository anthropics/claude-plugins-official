#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════╗
# ║  ARKHE SELF-MODELING — Substrato 890.6                          ║
# ║  Auto-modelagem: metacognição e autoconsciência funcional       ║
# ╚══════════════════════════════════════════════════════════════════╝

"""
Módulo de Self-Modeling para o World Model.

Implementa auto-modelagem funcional:
  - Modelo interno das próprias capacidades e limitações
  - Estimativa de confiança nas predições
  - Metacognição: "O que eu sei? O que eu não sei?"
  - Introspecção: análise das ativações internas

Arquitetura:
  Embedding unificado → Self-Model → (confidence, capability_vector, uncertainty_estimate)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple

class SelfModelingModule(nn.Module):
    """
    Módulo de auto-modelagem funcional.

    O modelo mantém uma representação interna de si mesmo:
      - Quais estágios estão ativos
      - Quão confiante está em cada predição
      - Quais são suas limitações atuais

    Args:
        d_model: dimensão do embedding unificado
        n_capabilities: número de capacidades modeladas
        n_uncertainty_levels: níveis de incerteza (alta/média/baixa)
    """

    def __init__(
        self,
        d_model: int = 512,
        n_capabilities: int = 6,  # 6 estágios
        n_uncertainty_levels: int = 3,
    ):
        super().__init__()
        self.d_model = d_model
        self.n_capabilities = n_capabilities
        self.n_uncertainty_levels = n_uncertainty_levels

        # Encoder de auto-representação
        self.self_encoder = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.LayerNorm(d_model),
            nn.ReLU(),
            nn.Linear(d_model, d_model // 2),
            nn.LayerNorm(d_model // 2),
            nn.ReLU(),
        )

        # Cabeças de predição
        self.confidence_head = nn.Sequential(
            nn.Linear(d_model // 2, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, 1),
            nn.Sigmoid(),
        )

        self.capability_head = nn.Sequential(
            nn.Linear(d_model // 2, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, n_capabilities),
            nn.Sigmoid(),
        )

        self.uncertainty_head = nn.Sequential(
            nn.Linear(d_model // 2, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, n_uncertainty_levels),
            nn.Softmax(dim=-1),
        )

        # Memória de episódios (para aprendizado contínuo)
        self.episodic_memory = []
        self.max_memory_size = 1000

        print(f"[890.6] SelfModelingModule: {d_model} dim, {n_capabilities} capabilities")

    def forward(self, fused_embedding: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Auto-modelagem a partir do embedding unificado.

        Args:
            fused_embedding: [batch, d_model] ou [d_model]

        Returns:
            self_model: dict com confidence, capabilities, uncertainty
        """
        if fused_embedding.dim() == 1:
            fused_embedding = fused_embedding.unsqueeze(0)
            squeeze = True
        else:
            squeeze = False

        # Encoder
        self_repr = self.self_encoder(fused_embedding)

        # Predições
        confidence = self.confidence_head(self_repr)  # [batch, 1]
        capabilities = self.capability_head(self_repr)  # [batch, n_capabilities]
        uncertainty = self.uncertainty_head(self_repr)  # [batch, n_uncertainty_levels]

        result = {
            "confidence": confidence.squeeze(-1) if squeeze else confidence,
            "capabilities": capabilities.squeeze(0) if squeeze else capabilities,
            "uncertainty": uncertainty.squeeze(0) if squeeze else uncertainty,
        }

        return result

    def introspect(self, fused_embedding: torch.Tensor) -> Dict[str, str]:
        """
        Introspecção: análise textual das capacidades atuais.

        Retorna descrição legível do estado interno do modelo.
        """
        with torch.no_grad():
            self_model = self.forward(fused_embedding)

        confidence = float(self_model["confidence"]) if self_model["confidence"].dim() == 0 else float(self_model["confidence"][0])
        capabilities = self_model["capabilities"].numpy() if self_model["capabilities"].dim() == 1 else self_model["capabilities"][0].numpy()
        uncertainty = self_model["uncertainty"].numpy() if self_model["uncertainty"].dim() == 1 else self_model["uncertainty"][0].numpy()

        capability_names = [
            "Token Grounding",
            "Physics Priors",
            "Multimodal Fusion",
            "Embodied Simulation",
            "Causal Reasoning",
            "Self-Modeling",
        ]

        uncertainty_labels = ["Baixa", "Média", "Alta"]
        max_unc_idx = int(uncertainty.argmax())

        report = {
            "confidence": f"{confidence:.1%}",
            "uncertainty_level": uncertainty_labels[max_unc_idx],
            "active_capabilities": ", ".join([
                name for name, val in zip(capability_names, capabilities)
                if val > 0.5
            ]),
            "capability_scores": {
                name: f"{val:.2f}" for name, val in zip(capability_names, capabilities)
            },
            "self_assessment": self._generate_assessment(confidence, uncertainty_labels[max_unc_idx], capabilities),
        }

        return report

    def _generate_assessment(self, confidence: float, uncertainty: str, capabilities) -> str:
        """Gera texto de auto-avaliação."""
        active = sum(1 for c in capabilities if c > 0.5)

        if confidence > 0.8 and uncertainty == "Baixa":
            return f"Estado operacional ótimo. {active}/6 capacidades ativas. Alta confiança nas predições."
        elif confidence > 0.5:
            return f"Estado operacional estável. {active}/6 capacidades ativas. Incerteza {uncertainty.lower()}."
        else:
            return f"Estado operacional degradado. {active}/6 capacidades ativas. Recomenda-se verificação humana."

    def store_episode(self, embedding: torch.Tensor, outcome: float, metadata: dict = None):
        """
        Armazena episódio na memória para aprendizado contínuo.

        Args:
            embedding: estado interno durante o episódio
            outcome: recompensa/outcome (0-1)
            metadata: informações adicionais
        """
        episode = {
            "embedding": embedding.detach().cpu(),
            "outcome": outcome,
            "metadata": metadata or {},
        }

        self.episodic_memory.append(episode)

        if len(self.episodic_memory) > self.max_memory_size:
            self.episodic_memory.pop(0)

    def reflect(self) -> Dict[str, float]:
        """
        Reflexão: análise da memória episódica para identificar padrões.

        Retorna estatísticas de desempenho ao longo do tempo.
        """
        if not self.episodic_memory:
            return {"mean_outcome": 0.0, "trend": 0.0, "n_episodes": 0}

        outcomes = [e["outcome"] for e in self.episodic_memory]

        mean_outcome = sum(outcomes) / len(outcomes)

        # Tendência: comparação primeira metade vs segunda metade
        mid = len(outcomes) // 2
        if mid > 0:
            first_half = sum(outcomes[:mid]) / mid
            second_half = sum(outcomes[mid:]) / (len(outcomes) - mid)
            trend = second_half - first_half
        else:
            trend = 0.0

        return {
            "mean_outcome": mean_outcome,
            "trend": trend,
            "n_episodes": len(outcomes),
            "best_outcome": max(outcomes),
            "worst_outcome": min(outcomes),
        }
