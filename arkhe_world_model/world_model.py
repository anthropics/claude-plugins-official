#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════╗
# ║  ARKHE WORLD MODEL EMBRYO — Orchestrator Principal              ║
# ║  Substrato 890 — CANONIZED_SPECULATIVE, H=2.0                   ║
# ╚══════════════════════════════════════════════════════════════════╝

"""
Orchestrator principal do World Model Embryo.

Integra os 6 estágios em um pipeline coeso:
  Stage 1: Token Grounding        → llm_engine
  Stage 2: Physics Priors         → physics_priors
  Stage 3: Multimodal Fusion      → multimodal_fusion
  Stage 4: Embodied Simulation    → brax_simulator
  Stage 5: Causal Reasoning       → causal_reasoning
  Stage 6: Self-Modeling          → self_model

Maturidade:
  embryo:  estágios 1-2 ativos, simulação stub
  infant:  estágios 1-4 ativos, simulação real
  adult:   todos os estágios, auto-modelagem completa
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum

class MaturityLevel(Enum):
    EMBRYO = "embryo"
    INFANT = "infant"
    ADULT = "adult"

class DevelopmentStage(Enum):
    TOKEN_GROUNDING = 1
    PHYSICS_PRIORS = 2
    MULTIMODAL_FUSION = 3
    EMBODIED_SIMULATION = 4
    CAUSAL_REASONING = 5
    SELF_MODELING = 6

@dataclass
class WorldModelConfig:
    """Configuração do World Model Embryo."""
    maturity: MaturityLevel = MaturityLevel.EMBRYO
    d_model: int = 512
    state_dim: int = 256
    n_vars: int = 10
    vocab_size: int = 32000
    max_seq_len: int = 4096

    # Pesos da loss híbrida
    lambda_ce: float = 1.0
    lambda_mse: float = 0.5
    lambda_causal: float = 0.3

    # Simulação
    sim_dt: float = 0.02
    sim_substeps: int = 10
    sim_scene: str = "pendulum"

    # Treinamento
    batch_size: int = 32
    learning_rate: float = 1e-4
    max_epochs: int = 100

    # RL
    rl_algorithm: str = "ppo"
    rl_timesteps: int = 100000

class WorldModelEmbryo(nn.Module):
    """
    Modelo de Mundo Embrionário ARKHE.

    Pipeline de processamento:
      texto → embedding LLM → grounding 2D/3D → fusão multimodal
      → simulação física → raciocínio causal → auto-modelagem

    Args:
        config: WorldModelConfig com hiperparâmetros
    """

    def __init__(self, config: Optional[WorldModelConfig] = None):
        super().__init__()
        self.config = config or WorldModelConfig()
        self.maturity = self.config.maturity
        self.active_stages = self._get_active_stages()

        # Módulos (lazy initialization)
        self._llm_engine = None
        self._physics_priors = None
        self._multimodal_fusion = None
        self._simulator = None
        self._causal_reasoner = None
        self._self_model = None

        # Estado interno
        self._current_stage = DevelopmentStage.TOKEN_GROUNDING
        self._training_history: List[Dict] = []
        self._is_trained = False

        print(f"[890] WorldModelEmbryo inicializado")
        print(f"[890] Maturidade: {self.maturity.value}")
        print(f"[890] Estágios ativos: {[s.name for s in self.active_stages]}")
        print(f"[890] d_model={self.config.d_model}, state_dim={self.config.state_dim}")
        print(f"[890] ⚠️  CANONIZED_SPECULATIVE — H=2.0 (alta incerteza)")

    def _get_active_stages(self) -> List[DevelopmentStage]:
        """Retorna estágios ativos baseado na maturidade."""
        if self.maturity == MaturityLevel.EMBRYO:
            return [
                DevelopmentStage.TOKEN_GROUNDING,
                DevelopmentStage.PHYSICS_PRIORS,
            ]
        elif self.maturity == MaturityLevel.INFANT:
            return [
                DevelopmentStage.TOKEN_GROUNDING,
                DevelopmentStage.PHYSICS_PRIORS,
                DevelopmentStage.MULTIMODAL_FUSION,
                DevelopmentStage.EMBODIED_SIMULATION,
            ]
        else:  # ADULT
            return list(DevelopmentStage)

    # ── Lazy getters ───────────────────────────────────────────

    @property
    def llm_engine(self):
        if self._llm_engine is None:
            from .llm_engine import ArkheLLMEngine
            self._llm_engine = ArkheLLMEngine(
                model_path="models/arkhe-os.gguf",
                n_ctx=self.config.max_seq_len,
            )
        return self._llm_engine

    @property
    def physics_priors(self):
        if self._physics_priors is None:
            from .physics_priors import PhysicsPriorsModule
            self._physics_priors = PhysicsPriorsModule(
                d_model=self.config.d_model,
                state_dim=self.config.state_dim,
            )
        return self._physics_priors

    @property
    def multimodal_fusion(self):
        if self._multimodal_fusion is None:
            from .multimodal_fusion import MultimodalFusionModule
            self._multimodal_fusion = MultimodalFusionModule(
                d_model=self.config.d_model,
                state_dim=self.config.state_dim,
            )
        return self._multimodal_fusion

    @property
    def simulator(self):
        if self._simulator is None:
            from .brax_simulator import ArkheBraxSimulator
            self._simulator = ArkheBraxSimulator(
                scene=self.config.sim_scene,
            )
        return self._simulator

    @property
    def causal_reasoner(self):
        if self._causal_reasoner is None:
            from .causal_reasoning import ArkheCausalReasoner
            self._causal_reasoner = ArkheCausalReasoner(
                n_vars=self.config.n_vars,
            )
        return self._causal_reasoner

    @property
    def self_model(self):
        if self._self_model is None:
            from .self_model import SelfModelingModule
            self._self_model = SelfModelingModule(
                d_model=self.config.d_model,
            )
        return self._self_model

    # ── Forward pass ───────────────────────────────────────────

    def forward(
        self,
        text_input: str,
        visual_input: Optional[np.ndarray] = None,
        action: Optional[np.ndarray] = None,
    ) -> Dict[str, np.ndarray]:
        """
        Passagem forward completa pelo pipeline do World Model.

        Args:
            text_input: descrição textual da cena/estado
            visual_input: imagem/frame opcional [H, W, C]
            action: ação a executar no simulador [action_dim]

        Returns:
            outputs: dict com embeddings e predições de cada estágio
        """
        outputs = {}

        # Stage 1: Token Grounding
        if DevelopmentStage.TOKEN_GROUNDING in self.active_stages:
            text, llm_emb = self.llm_engine.generate(text_input, max_tokens=256)
            grounding_2d = self.llm_engine.token_grounding_2d(llm_emb)
            outputs["stage1"] = {
                "text": text,
                "embedding": llm_emb,
                "grounding_2d": grounding_2d,
            }

        # Stage 2: Physics Priors
        if DevelopmentStage.PHYSICS_PRIORS in self.active_stages:
            physics_emb = self.physics_priors(llm_emb)
            outputs["stage2"] = {
                "physics_embedding": physics_emb,
            }

        # Stage 3: Multimodal Fusion
        if DevelopmentStage.MULTIMODAL_FUSION in self.active_stages:
            fused_emb = self.multimodal_fusion(
                text_emb=llm_emb,
                visual_emb=visual_input,
                physics_emb=physics_emb if DevelopmentStage.PHYSICS_PRIORS in self.active_stages else None,
            )
            outputs["stage3"] = {
                "fused_embedding": fused_emb,
            }

        # Stage 4: Embodied Simulation
        if DevelopmentStage.EMBODIED_SIMULATION in self.active_stages:
            sim_state = self.simulator.reset()
            if action is not None:
                sim_state = self.simulator.step(sim_state, action)
            world_emb = self.simulator.get_world_embedding(sim_state)
            outputs["stage4"] = {
                "sim_state": sim_state,
                "world_embedding": world_emb,
            }

        # Stage 5: Causal Reasoning
        if DevelopmentStage.CAUSAL_REASONING in self.active_stages:
            # Usar embedding do mundo como observação causal
            causal_data = world_emb[:self.config.n_vars].reshape(1, -1)
            if self.causal_reasoner.is_trained:
                factual, counter = self.causal_reasoner.counterfactual(
                    var_idx=0, value=1.0, observed=causal_data[0]
                )
                outputs["stage5"] = {
                    "factual": factual,
                    "counterfactual": counter,
                }

        # Stage 6: Self-Modeling
        if DevelopmentStage.SELF_MODELING in self.active_stages:
            self_emb = self.self_model(fused_emb if DevelopmentStage.MULTIMODAL_FUSION in self.active_stages else llm_emb)
            outputs["stage6"] = {
                "self_embedding": self_emb,
            }

        return outputs

    # ── Training ───────────────────────────────────────────────

    def fit(
        self,
        data_loader,
        epochs: Optional[int] = None,
        validate_every: int = 10,
    ) -> Dict[str, List[float]]:
        """
        Treina o World Model em um dataset multimodal.

        Args:
            data_loader: iterador de batches (texto, visual, estado, causal)
            epochs: número de épocas (usa config se None)
            validate_every: validar a cada N épocas

        Returns:
            history: dict com métricas de treinamento
        """
        from .losses import ArkheHybridLoss

        epochs = epochs or self.config.max_epochs

        # In case there are no parameters, use a dummy parameter so optimizer doesn't crash in demo mode
        params = list(self.parameters())
        if not params:
            self.dummy_param = nn.Parameter(torch.tensor([0.0], requires_grad=True))
            params = [self.dummy_param]

        optimizer = torch.optim.Adam(params, lr=self.config.learning_rate)
        criterion = ArkheHybridLoss(
            vocab_size=self.config.vocab_size,
            state_dim=self.config.state_dim,
            lambda_ce=self.config.lambda_ce,
            lambda_mse=self.config.lambda_mse,
            lambda_causal=self.config.lambda_causal,
        )

        history = {"total_loss": [], "ce_loss": [], "mse_loss": [], "causal_loss": []}

        for epoch in range(epochs):
            epoch_losses = {"total": 0.0, "ce": 0.0, "mse": 0.0, "causal": 0.0}
            n_batches = 0

            for batch in data_loader:
                optimizer.zero_grad()

                # Forward
                predictions = {}
                targets = {}

                # Stub: processar batch
                # Em produção: extrair logits, state_pred, causal_pred

                # Loss
                losses = criterion(predictions, targets, causal_model=self.causal_reasoner.scm if self._causal_reasoner else None)

                losses["total"].backward()
                optimizer.step()

                epoch_losses["total"] += losses["total"].item()
                epoch_losses["ce"] += losses["ce"].item()
                epoch_losses["mse"] += losses["mse"].item()
                epoch_losses["causal"] += losses["causal"].item()
                n_batches += 1

            # Médias
            for k in epoch_losses:
                epoch_losses[k] /= max(n_batches, 1)

            history["total_loss"].append(epoch_losses["total"])
            history["ce_loss"].append(epoch_losses["ce"])
            history["mse_loss"].append(epoch_losses["mse"])
            history["causal_loss"].append(epoch_losses["causal"])

            if epoch % validate_every == 0:
                print(f"[890] Epoch {epoch}/{epochs} | "
                      f"Loss: {epoch_losses['total']:.4f} | "
                      f"CE: {epoch_losses['ce']:.4f} | "
                      f"MSE: {epoch_losses['mse']:.4f} | "
                      f"Causal: {epoch_losses['causal']:.4f}")

        self._is_trained = True
        self._training_history.append(history)
        print(f"[890] Treinamento concluído: {epochs} épocas")

        return history

    # ── Inference ──────────────────────────────────────────────

    def predict(
        self,
        text_input: str,
        visual_input: Optional[np.ndarray] = None,
        action: Optional[np.ndarray] = None,
    ) -> Dict[str, np.ndarray]:
        """
        Predição completa (inference mode).
        """
        self.eval()
        with torch.no_grad():
            return self.forward(text_input, visual_input, action)

    def describe_scene(self, scene_state: dict) -> str:
        """
        Gera descrição textual de um estado físico.
        Stage 1 inverso: grounding físico → linguagem.
        """
        pos = scene_state.get("x", np.zeros(3))
        vel = scene_state.get("qd", np.zeros(6))[:3]
        return (
            f"Objeto em ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}) "
            f"com velocidade ({vel[0]:.2f}, {vel[1]:.2f}, {vel[2]:.2f})"
        )

    def counterfactual_query(
        self,
        observation: np.ndarray,
        intervention_var: int,
        intervention_value: float,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Query contrafactual: "O que aconteceria se...?"

        Args:
            observation: estado observado [n_vars]
            intervention_var: índice da variável a intervenir
            intervention_value: valor da intervenção

        Returns:
            (factual, counterfactual) — ambos [n_vars]
        """
        if DevelopmentStage.CAUSAL_REASONING not in self.active_stages:
            raise RuntimeError("Causal Reasoning não ativo nesta maturidade")

        if not self.causal_reasoner.is_trained:
            raise RuntimeError("Causal Reasoner não treinado. Chame fit() primeiro.")

        return self.causal_reasoner.counterfactual(
            intervention_var, intervention_value, observation
        )

    # ── Persistence ────────────────────────────────────────────

    def save(self, path: str):
        """Salva estado completo do World Model."""
        checkpoint = {
            "config": self.config,
            "maturity": self.maturity.value,
            "state_dict": self.state_dict(),
            "training_history": self._training_history,
            "is_trained": self._is_trained,
            "substrate": "890",
            "seal": "8d4e2f1a9c3b7e5d",
        }
        torch.save(checkpoint, path)
        print(f"[890] World Model salvo: {path}")

    def load(self, path: str):
        """Carrega estado completo do World Model."""
        checkpoint = torch.load(path)
        self.load_state_dict(checkpoint["state_dict"])
        self._training_history = checkpoint.get("training_history", [])
        self._is_trained = checkpoint.get("is_trained", False)
        print(f"[890] World Model carregado: {path}")
        print(f"[890] Treinado: {self._is_trained} | Histórico: {len(self._training_history)} runs")
