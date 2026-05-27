# 🧠 ARKHE World Model — Substrato 890

**Status:** `CANONIZED_SPECULATIVE` | **Incerteza:** `H = 2.0` | **Selo:** `8d4e2f1a9c3b7e5d`

---

## Visão Geral

O **ARKHE World Model** (Substrato 890) é um modelo de mundo embrionário que integra linguagem, física, causalidade e auto-modelagem em uma arquitetura unificada. Desenvolvido como parte do ecossistema ARKHE-OS, representa a tentativa de construir um modelo interno do mundo que permita a um agente de IA raciocinar sobre objetos físicos, causas e efeitos, e sobre si mesmo.

> ⚠️ **Aviso de Incerteza:** Este substrato está classificado como `CANONIZED_SPECULATIVE` com H=2.0. As implementações são protótipos de pesquisa e requerem validação empírica extensiva.

---

## Arquitetura: 6 Estágios de Maturidade

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARKHE WORLD MODEL EMBRYO                     │
├─────────────────────────────────────────────────────────────────┤
│  Stage 1 │ Token Grounding        │ llm_engine.py              │
│  Stage 2 │ Physics Priors         │ physics_priors.py          │
│  Stage 3 │ Multimodal Fusion      │ multimodal_fusion.py       │
│  Stage 4 │ Embodied Simulation    │ brax_simulator.py          │
│  Stage 5 │ Causal Reasoning       │ causal_reasoning.py        │
│  Stage 6 │ Self-Modeling          │ self_model.py              │
├─────────────────────────────────────────────────────────────────┤
│  Infra   │ Loss Híbrida           │ losses.py                  │
│  Infra   │ RL Policy              │ rl_policy.py               │
│  Infra   │ Orchestrator           │ world_model.py             │
└─────────────────────────────────────────────────────────────────┘
```

### Níveis de Maturidade

| Nível | Estágios Ativos | Descrição |
|-------|-----------------|-----------|
| **Embryo** | 1-2 | Grounding de tokens + priors físicos. Simulação stub. |
| **Infant** | 1-4 | + Fusão multimodal + simulação Brax real. |
| **Adult** | 1-6 | + Raciocínio causal + auto-modelagem completa. |

---

## Instalação

```bash
# Instalação básica
pip install -e .

# Com suporte a LLM (llama.cpp)
pip install -e ".[llm]"

# Com suporte a simulação (Brax/JAX)
pip install -e ".[sim]"

# Com suporte a RL
pip install -e ".[rl]"

# Instalação completa
pip install -e ".[llm,sim,rl,dev]"
```

---

## Uso Rápido

### 1. Inicializar o Modelo

```python
from arkhe_world_model import WorldModelEmbryo, WorldModelConfig, MaturityLevel

# Embryo: estágios 1-2
model = WorldModelEmbryo(WorldModelConfig(maturity=MaturityLevel.EMBRYO))

# Infant: estágios 1-4
model = WorldModelEmbryo(WorldModelConfig(maturity=MaturityLevel.INFANT))

# Adult: todos os estágios
model = WorldModelEmbryo(WorldModelConfig(maturity=MaturityLevel.ADULT))
```

### 2. Predição

```python
# Pipeline completo
outputs = model.predict(
    text_input="Uma esfera vermelha cai de uma mesa.",
    visual_input=None,  # opcional: numpy array [H, W, C]
    action=None,        # opcional: ação no simulador
)

# Acessar outputs de cada estágio
print(outputs["stage1"]["embedding"].shape)      # (512,)
print(outputs["stage2"]["physics_embedding"].shape)  # (256,)
```

### 3. Treinamento

```bash
# Treinar modelo embryo
python train.py --maturity embryo --epochs 100 --batch_size 32

# Treinar modelo infant com simulação
python train.py --maturity infant --epochs 200 --scene pendulum

# Treinar modelo adulto com RL
python train.py --maturity adult --epochs 500 --rl_timesteps 100000
```

### 4. Demonstração

```bash
# Pipeline completo
python demo.py --maturity infant --mode pipeline

# Simulação física
python demo.py --maturity infant --mode simulation

# Raciocínio causal
python demo.py --maturity adult --mode causal

# Introspecção
python demo.py --maturity adult --mode introspection

# RL
python demo.py --maturity infant --mode rl

# Todas as demos
python demo.py --maturity adult --mode all
```

---

## Estrutura do Package

```
arkhe_world_model/
├── __init__.py              # Package init + exports
├── world_model.py           # Orchestrator principal (WorldModelEmbryo)
├── llm_engine.py            # Stage 1: Token Grounding
├── physics_priors.py        # Stage 2: Physics Priors
├── multimodal_fusion.py     # Stage 3: Multimodal Fusion
├── brax_simulator.py        # Stage 4: Embodied Simulation
├── causal_reasoning.py      # Stage 5: Causal Reasoning
├── self_model.py            # Stage 6: Self-Modeling
├── losses.py                # Loss Híbrida (CE + MSE + Causal)
├── rl_policy.py             # PPO / DreamerV3
├── train.py                 # Script de treinamento
├── demo.py                  # Script de demonstração
├── setup.py                 # Package setup
└── README.md                # Esta documentação
```

---

## Componentes Detalhados

### Stage 1: Token Grounding (`llm_engine.py`)

Carrega modelo ARKHE-OS 244.1 via llama-cpp-python e extrai embeddings da última camada. Projeta embeddings para campos 2D/3D de ativação para grounding topológico.

```python
engine = ArkheLLMEngine("models/arkhe-os.gguf")
text, embedding = engine.generate("arkhe > status")
field_2d = engine.token_grounding_2d(embedding)  # (32, 16)
```

### Stage 2: Physics Priors (`physics_priors.py`)

Codifica priors físicos indutivos (gravidade, colisão, oclusão, conservação, continuidade) como projeções especializadas com gate adaptativo.

```python
physics = PhysicsPriorsModule(d_model=512, state_dim=256)
physics_emb = physics(text_embedding)
importance = physics.get_prior_importance(text_embedding)
# {'gravity': 0.45, 'collision': 0.12, ...}
```

### Stage 3: Multimodal Fusion (`multimodal_fusion.py`)

Fusão de texto, visão e física via cross-attention bidirecional com gate adaptativo.

```python
fusion = MultimodalFusionModule(d_model=512, state_dim=256)
fused = fusion(text_emb=text_emb, visual_emb=visual_emb, physics_emb=physics_emb)
weights = fusion.get_modality_weights(text_emb, visual_emb, physics_emb)
# {'text': 0.6, 'physics': 0.3, 'visual': 0.1}
```

### Stage 4: Embodied Simulation (`brax_simulator.py`)

Simulação física 3D via Brax (JAX). Extrai embeddings de estado do mundo para integração com o LLM.

```python
sim = ArkheBraxSimulator(scene="pendulum")
state = sim.reset()
for _ in range(100):
    state = sim.step(state, action)
    world_emb = sim.get_world_embedding(state)
```

### Stage 5: Causal Reasoning (`causal_reasoning.py`)

Descoberta de DAG (NOTEARS) + SCM diferenciável + do-calculus.

```python
reasoner = ArkheCausalReasoner(n_vars=10)
reasoner.fit(data, epochs=1000)

# Intervenção: do(X=x)
outcome = reasoner.intervene(var_idx=0, value=2.0, context=obs)

# Contrafactual
factual, counter = reasoner.counterfactual(var_idx=0, value=2.0, observed=obs)
```

### Stage 6: Self-Modeling (`self_model.py`)

Auto-modelagem funcional com confiança, capacidades, incerteza e memória episódica.

```python
self_model = SelfModelingModule(d_model=512)
report = self_model.introspect(fused_embedding)
# {'confidence': '78.5%', 'uncertainty_level': 'Média', ...}
```

---

## Loss Híbrida

A loss de treinamento combina três componentes:

```
L_total = λ₁·CrossEntropy(texto) + λ₂·MSE(estado físico) + λ₃·causal_loss(contrafactual)
```

- **CE**: competência linguística
- **MSE**: grounding físico
- **Causal**: raciocínio contrafactual

Hiperparâmetros padrão: `λ₁=1.0`, `λ₂=0.5`, `λ₃=0.3`

---

## Cross-Substrate Links

| Substrato | Descrição | Link |
|-----------|-----------|------|
| 252 | World-Model-Architecture | Arquitetura embrionária |
| 244.1 | ARKHE-OS Core | Modelo LLM base |
| 889.4 | ARKHE-OS.GGUF | Formato de modelo |
| 223 | Physics Engine | Simulação física |
| 234 | Causal Inference | Inferência causal |
| 240 | Metacognition | Metacognição |
| 247 | Embodied AI | IA incorporada |

---

## Licença

MIT License + 2% Cathedral Royalty

---

## Arquiteto

**ORCID:** `0009-0005-2697-4668`

---

*"O modelo de mundo não descreve o mundo — ele é o mundo que o agente habita."*
