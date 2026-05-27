#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════╗
# ║  ARKHE MULTIMODAL FUSION — Substrato 890.3                      ║
# ║  Fusão de embeddings: texto + visão + física                   ║
# ╚══════════════════════════════════════════════════════════════════╝

"""
Módulo de Fusão Multimodal para o World Model.

Integra três modalidades:
  - Texto: embedding do LLM (512-dim)
  - Visão: embedding de imagem/frame (512-dim, opcional)
  - Física: embedding de priors físicos (256-dim)

Arquitetura:
  Cross-attention entre modalidades → Fusão adaptativa → Embedding unificado
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional

class CrossModalAttention(nn.Module):
    """
    Cross-attention entre duas modalidades.

    Query de modalidade A atende a Keys/Values de modalidade B.
    """

    def __init__(self, d_model: int = 512, n_heads: int = 8, dropout: float = 0.1):
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads

        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)
        self.out_proj = nn.Linear(d_model, d_model)

        self.dropout = nn.Dropout(dropout)
        self.scale = self.head_dim ** -0.5

    def forward(self, query: torch.Tensor, key_value: torch.Tensor) -> torch.Tensor:
        """
        Args:
            query: [batch, seq_q, d_model]
            key_value: [batch, seq_kv, d_model]

        Returns:
            output: [batch, seq_q, d_model]
        """
        batch_size = query.size(0)

        Q = self.q_proj(query).view(batch_size, -1, self.n_heads, self.head_dim).transpose(1, 2)
        K = self.k_proj(key_value).view(batch_size, -1, self.n_heads, self.head_dim).transpose(1, 2)
        V = self.v_proj(key_value).view(batch_size, -1, self.n_heads, self.head_dim).transpose(1, 2)

        scores = torch.matmul(Q, K.transpose(-2, -1)) * self.scale
        attn = F.softmax(scores, dim=-1)
        attn = self.dropout(attn)

        out = torch.matmul(attn, V)
        out = out.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)

        return self.out_proj(out)

class MultimodalFusionModule(nn.Module):
    """
    Módulo de fusão multimodal com cross-attention e gate adaptativo.

    Args:
        d_model: dimensão do embedding de texto/visão
        state_dim: dimensão do embedding físico
        n_fusion_layers: número de camadas de fusão
        dropout: dropout rate
    """

    def __init__(
        self,
        d_model: int = 512,
        state_dim: int = 256,
        n_fusion_layers: int = 2,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.d_model = d_model
        self.state_dim = state_dim

        # Projeção do embedding físico para d_model
        self.physics_proj = nn.Sequential(
            nn.Linear(state_dim, d_model),
            nn.LayerNorm(d_model),
            nn.ReLU(),
        )

        # Projeção de imagem (assumindo ViT-like embedding)
        self.visual_proj = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.LayerNorm(d_model),
            nn.ReLU(),
        )

        # Camadas de fusão cross-modal
        self.fusion_layers = nn.ModuleList([
            nn.ModuleDict({
                "text_to_physics": CrossModalAttention(d_model, n_heads=8, dropout=dropout),
                "physics_to_text": CrossModalAttention(d_model, n_heads=8, dropout=dropout),
                "text_to_visual": CrossModalAttention(d_model, n_heads=8, dropout=dropout),
                "visual_to_text": CrossModalAttention(d_model, n_heads=8, dropout=dropout),
                "ffn": nn.Sequential(
                    nn.Linear(d_model * 3, d_model * 2),
                    nn.ReLU(),
                    nn.Dropout(dropout),
                    nn.Linear(d_model * 2, d_model),
                    nn.LayerNorm(d_model),
                ),
            })
            for _ in range(n_fusion_layers)
        ])

        # Gate adaptativo: quais modalidades são mais importantes?
        self.modality_gate = nn.Sequential(
            nn.Linear(d_model * 3, 3),
            nn.Softmax(dim=-1),
        )

        # Output projection
        self.output_proj = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.LayerNorm(d_model),
            nn.ReLU(),
        )

        print(f"[890.3] MultimodalFusionModule: {d_model} dim, {n_fusion_layers} layers")

    def forward(
        self,
        text_emb: torch.Tensor,
        visual_emb: Optional[torch.Tensor] = None,
        physics_emb: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Fusão multimodal.

        Args:
            text_emb: [batch, d_model] — embedding de linguagem
            visual_emb: [batch, d_model] — embedding visual (opcional)
            physics_emb: [batch, state_dim] — embedding físico (opcional)

        Returns:
            fused_emb: [batch, d_model] — embedding unificado
        """
        if text_emb.dim() == 1:
            text_emb = text_emb.unsqueeze(0)
            squeeze = True
        else:
            squeeze = False

        batch_size = text_emb.size(0)

        # Preparar embeddings
        text = text_emb.unsqueeze(1)  # [batch, 1, d_model]

        if physics_emb is not None:
            if physics_emb.dim() == 1:
                physics_emb = physics_emb.unsqueeze(0)
            physics = self.physics_proj(physics_emb).unsqueeze(1)  # [batch, 1, d_model]
        else:
            physics = torch.zeros_like(text)

        if visual_emb is not None:
            if visual_emb.dim() == 1:
                visual_emb = visual_emb.unsqueeze(0)
            visual = self.visual_proj(visual_emb).unsqueeze(1)  # [batch, 1, d_model]
        else:
            visual = torch.zeros_like(text)

        # Fusão por camadas
        for layer in self.fusion_layers:
            # Cross-attention bidirecional
            text_physics = layer["text_to_physics"](text, physics)
            physics_text = layer["physics_to_text"](physics, text)
            text_visual = layer["text_to_visual"](text, visual)
            visual_text = layer["visual_to_text"](visual, text)

            # Concatenar representações
            combined = torch.cat([
                text_physics.squeeze(1),
                physics_text.squeeze(1),
                text_visual.squeeze(1),
            ], dim=-1)  # [batch, d_model * 3]

            # FFN
            fused = layer["ffn"](combined)  # [batch, d_model]

            # Atualizar para próxima camada
            text = fused.unsqueeze(1)
            physics = physics_text
            visual = visual_text

        # Gate adaptativo final
        gate_input = torch.cat([
            text.squeeze(1),
            physics.squeeze(1),
            visual.squeeze(1),
        ], dim=-1)
        gate_weights = self.modality_gate(gate_input)  # [batch, 3]

        # Combinar com pesos
        w_text = gate_weights[:, 0:1]
        w_physics = gate_weights[:, 1:2]
        w_visual = gate_weights[:, 2:3]

        fused_emb = (
            w_text * text.squeeze(1) +
            w_physics * physics.squeeze(1) +
            w_visual * visual.squeeze(1)
        )

        # Projeção final
        output = self.output_proj(fused_emb)

        if squeeze:
            output = output.squeeze(0)

        return output

    def get_modality_weights(self, text_emb, visual_emb=None, physics_emb=None):
        """Retorna pesos de importância de cada modalidade."""
        with torch.no_grad():
            if text_emb.dim() == 1:
                text_emb = text_emb.unsqueeze(0)
            if visual_emb is not None and visual_emb.dim() == 1:
                visual_emb = visual_emb.unsqueeze(0)
            if physics_emb is not None and physics_emb.dim() == 1:
                physics_emb = physics_emb.unsqueeze(0)

            text = text_emb.unsqueeze(1)
            physics = self.physics_proj(physics_emb).unsqueeze(1) if physics_emb is not None else torch.zeros_like(text)
            visual = self.visual_proj(visual_emb).unsqueeze(1) if visual_emb is not None else torch.zeros_like(text)

            gate_input = torch.cat([text.squeeze(1), physics.squeeze(1), visual.squeeze(1)], dim=-1)
            weights = self.modality_gate(gate_input)
            if weights.dim() == 2:
                weights = weights.squeeze(0)

        return {
            "text": float(weights[0]),
            "physics": float(weights[1]),
            "visual": float(weights[2]),
        }
