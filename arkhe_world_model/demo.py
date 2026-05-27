#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════╗
# ║  ARKHE WORLD MODEL — Demonstração Interativa                    ║
# ║  Substrato 890 — Demo Script                                    ║
# ╚══════════════════════════════════════════════════════════════════╝

"""
Script de demonstração do World Model Embryo.

Uso:
    python demo.py --maturity embryo --mode pipeline
    python demo.py --maturity infant --mode simulation
    python demo.py --maturity adult --mode causal
    python demo.py --mode introspection
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))

from arkhe_world_model import WorldModelEmbryo, WorldModelConfig, MaturityLevel


def demo_pipeline(model: WorldModelEmbryo):
    """Demonstra o pipeline completo de forward pass."""
    print("\n" + "═" * 60)
    print("  DEMO: Pipeline Completo (Forward Pass)")
    print("═" * 60)

    text_input = "Uma esfera vermelha cai de uma mesa e colide com o chão."

    print(f"\n  Entrada: \"{text_input}\"")
    print(f"  Maturidade: {model.maturity.value}")
    print(f"  Estágios ativos: {[s.name for s in model.active_stages]}")

    outputs = model.predict(text_input)

    for stage_name, stage_output in outputs.items():
        print(f"\n  📦 {stage_name.upper()}")
        for key, value in stage_output.items():
            if isinstance(value, np.ndarray):
                print(f"     {key}: shape={value.shape}, dtype={value.dtype}")
            elif isinstance(value, str):
                print(f"     {key}: \"{value[:80]}...\"" if len(value) > 80 else f"     {key}: \"{value}\"")
            else:
                print(f"     {key}: {value}")


def demo_simulation(model: WorldModelEmbryo):
    """Demonstra simulação física."""
    print("\n" + "═" * 60)
    print("  DEMO: Simulação Física (Brax)")
    print("═" * 60)

    if model.simulator is None:
        print("  ⚠️  Simulador não disponível nesta maturidade")
        return

    print(f"  Cena: {model.config.sim_scene}")
    print(f"  dt: {model.config.sim_dt}s | Substeps: {model.config.sim_substeps}")

    state = model.simulator.reset(seed=42)
    print(f"\n  Estado inicial: {state}")

    # Simular 10 passos
    for step in range(10):
        action = np.random.randn(6) * 0.1  # pequena perturbação
        state = model.simulator.step(state, action)
        world_emb = model.simulator.get_world_embedding(state)

        if step % 3 == 0:
            print(f"  Step {step}: pos=({state['x'][0]:.3f}, {state['x'][1]:.3f}, {state['x'][2]:.3f}) | "
                  f"world_emb norm={np.linalg.norm(world_emb):.3f}")

    # Trajectory embedding
    traj_emb = model.simulator.get_trajectory_embedding(window=5)
    print(f"\n  Trajectory embedding: shape={traj_emb.shape}, norm={np.linalg.norm(traj_emb):.3f}")


def demo_causal(model: WorldModelEmbryo):
    """Demonstra raciocínio causal."""
    print("\n" + "═" * 60)
    print("  DEMO: Raciocínio Causal (SCM)")
    print("═" * 60)

    if model.causal_reasoner is None:
        print("  ⚠️  Raciocínio causal não disponível nesta maturidade")
        return

    # Gerar dados sintéticos e treinar SCM
    print("\n  Gerando dados sintéticos...")
    n_samples = 500
    n_vars = model.config.n_vars
    data = np.random.randn(n_samples, n_vars).astype(np.float32)

    # Criar relação causal simples: X0 → X1 → X2
    data[:, 1] = 0.7 * data[:, 0] + 0.3 * np.random.randn(n_samples)
    data[:, 2] = 0.5 * data[:, 1] + 0.5 * np.random.randn(n_samples)

    print(f"  Treinando SCM ({n_samples} amostras, {n_vars} variáveis)...")
    model.causal_reasoner.fit(data, epochs=500, lr=1e-3)

    # Intervenção
    print("\n  🔬 Intervenção: do(X₀ = 2.0)")
    context = data[0]
    outcome = model.causal_reasoner.intervene(0, 2.0, context)
    print(f"  Contexto: {context[:5]}")
    print(f"  Resultado: {outcome[:5]}")

    # Contrafactual
    print("\n  🔮 Contrafactual: 'E se X₀ fosse 2.0?'")
    observed = data[1]
    factual, counter = model.causal_reasoner.counterfactual(0, 2.0, observed)
    print(f"  Observado: {observed[:5]}")
    print(f"  Factual:   {factual[:5]}")
    print(f"  Counter:   {counter[:5]}")
    print(f"  Diferença: {np.abs(counter - factual)[:5]}")


def demo_introspection(model: WorldModelEmbryo):
    """Demonstra auto-modelagem e introspecção."""
    print("\n" + "═" * 60)
    print("  DEMO: Introspecção (Self-Modeling)")
    print("═" * 60)

    if model.self_model is None:
        print("  ⚠️  Self-modeling não disponível nesta maturidade")
        return

    # Criar embedding sintético
    fused_emb = torch.randn(1, model.config.d_model)

    # Introspecção
    report = model.self_model.introspect(fused_emb)

    print("\n  📋 Relatório de Auto-Modelagem:")
    print(f"  ┌─────────────────────────────────────────────┐")
    print(f"  │ Confiança:           {report['confidence']:>20} │")
    print(f"  │ Incerteza:           {report['uncertainty_level']:>20} │")
    print(f"  │ Capacidades ativas:  {report['active_capabilities']:>20} │")
    print(f"  │ Auto-avaliação:      {report['self_assessment'][:40]:>20}... │")
    print(f"  └─────────────────────────────────────────────┘")

    print("\n  📊 Scores de Capacidade:")
    for cap, score in report["capability_scores"].items():
        bar = "█" * int(float(score) * 20)
        print(f"     {cap:25s} [{bar:<20}] {score}")

    # Armazenar episódios
    print("\n  💾 Armazenando episódios...")
    for i in range(10):
        emb = torch.randn(model.config.d_model)
        outcome = np.random.random()
        model.self_model.store_episode(emb, outcome, {"episode": i})

    # Reflexão
    reflection = model.self_model.reflect()
    print(f"\n  🪞 Reflexão:")
    print(f"     Episódios: {reflection['n_episodes']}")
    print(f"     Outcome médio: {reflection['mean_outcome']:.3f}")
    print(f"     Tendência: {'↗' if reflection['trend'] > 0 else '↘' if reflection['trend'] < 0 else '→'} {reflection['trend']:+.3f}")
    print(f"     Melhor: {reflection['best_outcome']:.3f} | Pior: {reflection['worst_outcome']:.3f}")


def demo_rl(model: WorldModelEmbryo):
    """Demonstra treinamento RL."""
    print("\n" + "═" * 60)
    print("  DEMO: Reinforcement Learning (PPO)")
    print("═" * 60)

    from arkhe_world_model.rl_policy import WorldModelEnv, PPOPolicy

    env = WorldModelEnv(
        simulator=model.simulator,
        llm_engine=model.llm_engine,
        max_steps=100,
    )

    policy = PPOPolicy(
        obs_dim=env.observation_space,
        action_dim=env.action_space,
    )

    print(f"  Observation space: {env.observation_space}")
    print(f"  Action space: {env.action_space}")

    # Simular um episódio
    obs = env.reset()
    total_reward = 0.0

    print("\n  Simulando episódio...")
    for step in range(20):
        action, log_prob, value = policy.get_action(obs)
        obs, reward, done, truncated, info = env.step(action)
        total_reward += reward

        if step % 5 == 0:
            print(f"  Step {step}: reward={reward:.4f} | coherence={info['coherence']:.4f}")

        if done or truncated:
            break

    print(f"\n  Recompensa total: {total_reward:.4f}")


def main():
    parser = argparse.ArgumentParser(description="Demo do ARKHE World Model")
    parser.add_argument("--maturity", type=str, default="embryo",
                        choices=["embryo", "infant", "adult"],
                        help="Nível de maturidade")
    parser.add_argument("--mode", type=str, default="pipeline",
                        choices=["pipeline", "simulation", "causal", "introspection", "rl", "all"],
                        help="Modo de demonstração")
    parser.add_argument("--checkpoint", type=str, default=None,
                        help="Path para checkpoint (opcional)")

    args = parser.parse_args()

    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 12 + "ARKHE WORLD MODEL — DEMO" + " " * 22 + "║")
    print("║" + " " * 8 + "Substrato 890 | CANONIZED_SPECULATIVE" + " " * 11 + "║")
    print("║" + " " * 18 + "H = 2.0 (alta incerteza)" + " " * 16 + "║")
    print("╚" + "═" * 58 + "╝")

    # Configurar modelo
    maturity_map = {
        "embryo": MaturityLevel.EMBRYO,
        "infant": MaturityLevel.INFANT,
        "adult": MaturityLevel.ADULT,
    }

    config = WorldModelConfig(maturity=maturity_map[args.maturity])
    model = WorldModelEmbryo(config)

    if args.checkpoint:
        model.load(args.checkpoint)

    # Executar demos
    modes = ["pipeline", "simulation", "causal", "introspection", "rl"] if args.mode == "all" else [args.mode]

    for mode in modes:
        if mode == "pipeline":
            demo_pipeline(model)
        elif mode == "simulation":
            demo_simulation(model)
        elif mode == "causal":
            demo_causal(model)
        elif mode == "introspection":
            demo_introspection(model)
        elif mode == "rl":
            demo_rl(model)

    print("\n" + "═" * 60)
    print("  Demo concluída!")
    print("═" * 60)


if __name__ == "__main__":
    main()
