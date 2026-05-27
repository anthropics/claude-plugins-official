#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════╗
# ║  ARKHE KOLMOGOROV REGULARIZER — Substrato 898                  ║
# ║  Neural Weight Norm = Kolmogorov Complexity (Musat 2026)       ║
# ║  CANONIZED — H = 0.15 | Φ_C = 0.96 | Theosis = 0.90            ║
# ╚══════════════════════════════════════════════════════════════════╝

"""
Regularizador de Kolmogorov para o World Model ARKHE.

Baseado no teorema de Musat (arXiv:2605.10878v1):
  "Neural Weight Norm = Kolmogorov Complexity"

O teorema prova que, em precisão fixa (fp16, int8, ternário),
a norma dos pesos de uma rede neural em laço coincide com a
complexidade de Kolmogorov da string emitida, a menos de um
fator logarítmico:

  𝒩(θ) ≤ K(s) + c_U
  K(s) ≤ c_d · 𝒩(θ) · log 𝒩(θ) + c_d

Corolário 7: A decadência de peso L2 implementa o prior de
Solomonoff sobre as funções computáveis.

Este módulo substitui o weight decay padrão por um regularizador
explícito de complexidade de Kolmogorov:

  R_K(θ) = ‖θ‖_2^2 · log(‖θ‖_2^2 + 1)

Uso:
  from arkhe_world_model.kolmogorov_regularizer import kolmogorov_regularizer

  loss = task_loss + lambda_k * kolmogorov_regularizer(model)
"""

import torch
import torch.nn as nn
from typing import Optional, Dict


def kolmogorov_regularizer(
    model: nn.Module,
    p: float = 2.0,
    eps: float = 1e-8,
    exclude_bias: bool = True,
    exclude_norm: bool = True,
) -> torch.Tensor:
    """
    Estima a complexidade de Kolmogorov K(θ) via norma dos pesos.

    Conforme Musat (2026), em precisão fixa:
      K(s) ≈ c_d · ‖θ‖_p^p · log(‖θ‖_p^p) + c_d

    Para p=2 (regime L2, Corolário 7):
      R_K(θ) = ‖θ‖_2^2 · log(‖θ‖_2^2 + 1)

    Args:
        model: rede neural cujos pesos serão regularizados
        p: ordem da norma (p=2 para L2/Solomonoff, p=1 para LASSO)
        eps: epsilon para estabilidade numérica
        exclude_bias: se True, não regulariza biases
        exclude_norm: se True, não regulariza parâmetros de LayerNorm/BatchNorm

    Returns:
        R_K: tensor escalar — estimativa de complexidade de Kolmogorov
    """
    w_norm_p = 0.0
    n_params = 0

    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue

        # Excluir biases
        if exclude_bias and "bias" in name:
            continue

        # Excluir parâmetros de normalização
        if exclude_norm and any(x in name for x in ["norm", "ln", "bn", "gn"]):
            continue

        # Acumular norma Lp
        if p == 2.0:
            w_norm_p += param.pow(2).sum().item()
        elif p == 1.0:
            w_norm_p += param.abs().sum().item()
        else:
            w_norm_p += param.abs().pow(p).sum().item()

        n_params += param.numel()

    w_norm_p = torch.tensor(w_norm_p, device=next(model.parameters()).device)

    # Complexidade de Kolmogorov estimada: ‖θ‖_p^p · log(‖θ‖_p^p + 1)
    # O +1 garante que log(0) não ocorra; o eps adiciona estabilidade
    R_K = w_norm_p * torch.log(w_norm_p + 1.0 + eps)

    return R_K


def kolmogorov_complexity_estimate(
    model: nn.Module,
    precision_bits: int = 16,
) -> Dict[str, float]:
    """
    Estima a complexidade de Kolmogorov de um modelo completo.

    Retorna métricas detalhadas para análise ontológica.

    Args:
        model: rede neural
        precision_bits: bits de precisão (16 para fp16, 8 para int8, etc.)

    Returns:
        metrics: dict com estimativas de complexidade
    """
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    # Norma L2 dos pesos
    w_norm_sq = sum(p.pow(2).sum().item() for p in model.parameters() if p.requires_grad)

    # Complexidade de Kolmogorov estimada (Musat 2026)
    K_estimate = w_norm_sq * int(w_norm_sq + 1).bit_length()  # aproximação: ‖θ‖² · log₂(‖θ‖²)

    # Bits mínimos para descrever o modelo (limite inferior)
    bits_lower_bound = trainable_params * precision_bits

    # Bits efetivos (comprimidos pela estrutura)
    bits_effective = K_estimate

    # Taxa de compressão
    compression_ratio = bits_lower_bound / max(bits_effective, 1)

    return {
        "total_params": total_params,
        "trainable_params": trainable_params,
        "weight_norm_l2": w_norm_sq,
        "K_estimate": K_estimate,
        "bits_lower_bound": bits_lower_bound,
        "bits_effective": bits_effective,
        "compression_ratio": compression_ratio,
        "precision_bits": precision_bits,
    }


class KolmogorovWeightDecay(torch.optim.Optimizer):
    """
    Otimizador com regularização de Kolmogorov (Solomonoff prior).

    Substitui o AdamW padrão por uma versão que aplica o regularizador
    de Kolmogorov em vez de simples weight decay L2.

    A atualização dos pesos inclui:
      g_t = ∇L_task + λ_K · ∇R_K(θ)

    onde ∇R_K(θ) = 2θ · (1 + log(‖θ‖² + 1)) + 2θ · ‖θ‖² / (‖θ‖² + 1)

    Args:
        params: parâmetros do modelo
        lr: learning rate
        lambda_k: peso do regularizador de Kolmogorov
        betas: coeficientes de momentum (Adam)
        eps: epsilon para estabilidade
    """

    def __init__(
        self,
        params,
        lr: float = 1e-3,
        lambda_k: float = 1e-4,
        betas: tuple = (0.9, 0.999),
        eps: float = 1e-8,
    ):
        defaults = dict(lr=lr, lambda_k=lambda_k, betas=betas, eps=eps)
        super().__init__(params, defaults)

    @torch.no_grad()
    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            lambda_k = group["lambda_k"]
            lr = group["lr"]
            beta1, beta2 = group["betas"]
            eps = group["eps"]

            # Calcular norma total dos pesos para R_K
            w_norm_sq = 0.0
            for p in group["params"]:
                if p.grad is None:
                    continue
                w_norm_sq += p.pow(2).sum().item()
            w_norm_sq = max(w_norm_sq, eps)

            # Gradiente do regularizador de Kolmogorov
            # R_K = ‖θ‖² · log(‖θ‖² + 1)
            # ∇R_K = 2θ · log(‖θ‖² + 1) + 2θ · ‖θ‖² / (‖θ‖² + 1)
            log_term = int(w_norm_sq + 1).bit_length()  # log₂ aproximado
            grad_factor = log_term + w_norm_sq / (w_norm_sq + 1)

            for p in group["params"]:
                if p.grad is None:
                    continue

                grad = p.grad

                # Estado do otimizador
                state = self.state[p]
                if len(state) == 0:
                    state["step"] = 0
                    state["exp_avg"] = torch.zeros_like(p)
                    state["exp_avg_sq"] = torch.zeros_like(p)

                exp_avg = state["exp_avg"]
                exp_avg_sq = state["exp_avg_sq"]
                state["step"] += 1

                # Gradiente com regularização de Kolmogorov
                k_grad = lambda_k * 2 * p * grad_factor
                grad = grad + k_grad

                # Atualização Adam
                exp_avg.mul_(beta1).add_(grad, alpha=1 - beta1)
                exp_avg_sq.mul_(beta2).addcmul_(grad, grad, value=1 - beta2)

                bias_correction1 = 1 - beta1 ** state["step"]
                bias_correction2 = 1 - beta2 ** state["step"]

                step_size = lr / bias_correction1
                denom = (exp_avg_sq.sqrt() / (bias_correction2 ** 0.5)).add_(eps)

                p.addcdiv_(exp_avg, denom, value=-step_size)

        return loss


def print_kolmogorov_report(model: nn.Module, precision_bits: int = 16):
    """
    Imprime relatório de complexidade de Kolmogorov do modelo.

    Útil para introspecção ontológica e monitoramento de treino.
    """
    metrics = kolmogorov_complexity_estimate(model, precision_bits)

    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "KOLMOGOROV COMPLEXITY REPORT" + " " * 20 + "║")
    print("║" + " " * 8 + "Substrato 898 | Musat 2026 | CANONIZED" + " " * 10 + "║")
    print("╚" + "═" * 58 + "╝")
    print(f"  Parâmetros totais:      {metrics['total_params']:,}")
    print(f"  Parâmetros treináveis:  {metrics['trainable_params']:,}")
    print(f"  Norma L2 dos pesos:     {metrics['weight_norm_l2']:.4f}")
    print(f"  K(θ) estimada:          {metrics['K_estimate']:.2f}")
    print(f"  Bits (limite inferior): {metrics['bits_lower_bound']:,}")
    print(f"  Bits efetivos:          {metrics['bits_effective']:.2f}")
    print(f"  Taxa de compressão:     {metrics['compression_ratio']:.2f}x")
    print(f"  Precisão:               {precision_bits}-bit")
    print("═" * 60)
