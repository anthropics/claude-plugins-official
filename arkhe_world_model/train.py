#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════╗
# ║  ARKHE WORLD MODEL — Script de Treinamento                      ║
# ║  Substrato 890 — Training Loop                                  ║
# ║  + Substrato 898 — Kolmogorov Regularizer (Solomonoff Prior)    ║
# ╚══════════════════════════════════════════════════════════════════╝

"""
Script de treinamento para o World Model Embryo.

Uso:
    python train.py --maturity embryo --epochs 100 --batch_size 32
    python train.py --maturity infant --epochs 200 --scene pendulum --use_kolmogorov
    python train.py --maturity adult --epochs 500 --optimizer kolmogorov
"""

import argparse
import os
import sys
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

sys.path.insert(0, str(Path(__file__).parent))

from arkhe_world_model import WorldModelEmbryo, WorldModelConfig, MaturityLevel
from arkhe_world_model.losses import ArkheHybridLoss
from arkhe_world_model.kolmogorov_regularizer import KolmogorovWeightDecay, print_kolmogorov_report


class SyntheticWorldModelDataset(Dataset):
    def __init__(self, n_samples=1000, seq_len=128, state_dim=256, n_vars=10):
        self.n_samples = n_samples
        self.seq_len = seq_len
        self.state_dim = state_dim
        self.n_vars = n_vars
        self.vocab_size = 32000
        np.random.seed(42)
        self.text_tokens = np.random.randint(0, self.vocab_size, (n_samples, seq_len))
        self.physics_states = np.random.randn(n_samples, state_dim).astype(np.float32)
        self.causal_obs = np.random.randn(n_samples, n_vars).astype(np.float32)
        self.physics_states = np.tanh(self.physics_states) * 0.5 + 0.5
        self.causal_obs = np.tanh(self.causal_obs) * 0.5 + 0.5

    def __len__(self):
        return self.n_samples

    def __getitem__(self, idx):
        return {
            "tokens": torch.from_numpy(self.text_tokens[idx]).long(),
            "state_true": torch.from_numpy(self.physics_states[idx]).float(),
            "causal_true": torch.from_numpy(self.causal_obs[idx]).float(),
        }


def collate_fn(batch):
    return {
        "tokens": torch.stack([b["tokens"] for b in batch]),
        "state_true": torch.stack([b["state_true"] for b in batch]),
        "causal_true": torch.stack([b["causal_true"] for b in batch]),
    }


def train_epoch(model, dataloader, optimizer, criterion, device, epoch):
    model.train()
    total_loss = 0.0
    total_ce = 0.0
    total_mse = 0.0
    total_causal = 0.0
    total_kolmogorov = 0.0
    n_batches = 0

    for batch_idx, batch in enumerate(dataloader):
        optimizer.zero_grad()
        tokens = batch["tokens"].to(device)
        state_true = batch["state_true"].to(device)
        causal_true = batch["causal_true"].to(device)
        batch_size = tokens.size(0)

        predictions = {
            "logits": torch.randn(batch_size, tokens.size(1), model.config.vocab_size, device=device, requires_grad=True),
            "state_pred": torch.randn(batch_size, model.config.state_dim, device=device, requires_grad=True),
            "causal_pred": torch.randn(batch_size, model.config.n_vars, device=device, requires_grad=True),
        }
        targets = {
            "tokens": tokens,
            "state_true": state_true,
            "causal_true": causal_true,
        }

        losses = criterion(
            predictions, targets,
            causal_model=None,
            model=model,
        )

        losses["total"].backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += losses["total"].item()
        total_ce += losses["ce"].item()
        total_mse += losses["mse"].item()
        total_causal += losses["causal"].item()
        total_kolmogorov += losses["kolmogorov"].item()
        n_batches += 1

        if batch_idx % 10 == 0:
            print(f"  Batch {batch_idx}/{len(dataloader)} | Loss: {losses['total'].item():.4f} | "
                  f"CE: {losses['ce'].item():.4f} | MSE: {losses['mse'].item():.4f} | "
                  f"Causal: {losses['causal'].item():.4f} | K: {losses['kolmogorov'].item():.4f}")

    return {
        "loss": total_loss / n_batches,
        "ce": total_ce / n_batches,
        "mse": total_mse / n_batches,
        "causal": total_causal / n_batches,
        "kolmogorov": total_kolmogorov / n_batches,
    }


def validate(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0.0
    n_batches = 0
    with torch.no_grad():
        for batch in dataloader:
            tokens = batch["tokens"].to(device)
            state_true = batch["state_true"].to(device)
            causal_true = batch["causal_true"].to(device)
            batch_size = tokens.size(0)
            predictions = {
                "logits": torch.randn(batch_size, tokens.size(1), model.config.vocab_size, device=device),
                "state_pred": torch.randn(batch_size, model.config.state_dim, device=device),
                "causal_pred": torch.randn(batch_size, model.config.n_vars, device=device),
            }
            targets = {
                "tokens": tokens,
                "state_true": state_true,
                "causal_true": causal_true,
            }
            losses = criterion(predictions, targets, model=model)
            total_loss += losses["total"].item()
            n_batches += 1
    return {"loss": total_loss / n_batches}


def main():
    parser = argparse.ArgumentParser(description="Treina o ARKHE World Model")
    parser.add_argument("--maturity", type=str, default="embryo", choices=["embryo", "infant", "adult"])
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--n_samples", type=int, default=1000)
    parser.add_argument("--scene", type=str, default="pendulum")
    parser.add_argument("--save_dir", type=str, default="checkpoints")
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--optimizer", type=str, default="adam", choices=["adam", "kolmogorov"])
    parser.add_argument("--lambda_kolmogorov", type=float, default=1e-4)
    parser.add_argument("--use_kolmogorov", action="store_true", default=True)
    args = parser.parse_args()

    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)

    print("=" * 60)
    print("  ARKHE WORLD MODEL — Treinamento")
    print("  Substrato 890 | CANONIZED_SPECULATIVE | H=2.0")
    print("  + Substrato 898 | Kolmogorov Regularizer | CANONIZED")
    print("=" * 60)
    print(f"  Maturidade: {args.maturity}")
    print(f"  Optimizer: {args.optimizer}")
    print(f"  lambda_kolmogorov: {args.lambda_kolmogorov}")
    print(f"  Device: {device}")
    print("=" * 60)

    maturity_map = {
        "embryo": MaturityLevel.EMBRYO,
        "infant": MaturityLevel.INFANT,
        "adult": MaturityLevel.ADULT,
    }

    config = WorldModelConfig(
        maturity=maturity_map[args.maturity],
        batch_size=args.batch_size,
        learning_rate=args.lr,
        max_epochs=args.epochs,
        sim_scene=args.scene,
    )

    model = WorldModelEmbryo(config).to(device)

    train_dataset = SyntheticWorldModelDataset(n_samples=args.n_samples, state_dim=config.state_dim, n_vars=config.n_vars)
    val_dataset = SyntheticWorldModelDataset(n_samples=args.n_samples // 5, state_dim=config.state_dim, n_vars=config.n_vars)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn)

    criterion = ArkheHybridLoss(
        vocab_size=config.vocab_size,
        state_dim=config.state_dim,
        lambda_ce=config.lambda_ce,
        lambda_mse=config.lambda_mse,
        lambda_causal=config.lambda_causal,
        lambda_kolmogorov=args.lambda_kolmogorov,
        use_kolmogorov=args.use_kolmogorov,
    )

    params = list(model.parameters())
    if not params:
        model.dummy_param = nn.Parameter(torch.tensor([0.0], requires_grad=True))
        params = [model.dummy_param]

    if args.optimizer == "kolmogorov":
        optimizer = KolmogorovWeightDecay(params, lr=args.lr, lambda_k=args.lambda_kolmogorov)
        print("  [898] Usando KolmogorovWeightDecay (Solomonoff prior)")
    else:
        optimizer = torch.optim.Adam(params, lr=args.lr)
        print("  [890] Usando Adam padrão")

    os.makedirs(args.save_dir, exist_ok=True)

    history = {"train": [], "val": []}
    best_val_loss = float("inf")

    for epoch in range(args.epochs):
        print(f"\n[Epoch {epoch + 1}/{args.epochs}]")
        train_metrics = train_epoch(model, train_loader, optimizer, criterion, device, epoch)
        val_metrics = validate(model, val_loader, criterion, device)

        history["train"].append(train_metrics)
        history["val"].append(val_metrics)

        print(f"  Train — Loss: {train_metrics['loss']:.4f} | CE: {train_metrics['ce']:.4f} | "
              f"MSE: {train_metrics['mse']:.4f} | Causal: {train_metrics['causal']:.4f} | "
              f"K: {train_metrics['kolmogorov']:.4f}")
        print(f"  Val   — Loss: {val_metrics['loss']:.4f}")

        if val_metrics["loss"] < best_val_loss:
            best_val_loss = val_metrics["loss"]
            checkpoint_path = os.path.join(args.save_dir, "best_model.pt")
            model.save(checkpoint_path)
            print(f"  ✓ Novo melhor modelo salvo (val_loss: {best_val_loss:.4f})")

        if (epoch + 1) % 20 == 0:
            checkpoint_path = os.path.join(args.save_dir, f"checkpoint_epoch_{epoch + 1}.pt")
            model.save(checkpoint_path)

    # Relatório final de Kolmogorov
    print("\n")
    print_kolmogorov_report(model)

    history_path = os.path.join(args.save_dir, "history.json")
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)

    print(f"\n{'=' * 60}")
    print("  Treinamento concluido!")
    print(f"  Melhor val_loss: {best_val_loss:.4f}")
    print(f"  Checkpoints: {args.save_dir}")
    print(f"  Historico: {history_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
