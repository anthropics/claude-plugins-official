---
name: evolve-ml
description: ML subskill for /evolve - optimizes model accuracy and performance (STUB)
version: 1.0.0
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, TodoWrite, WebSearch, WebFetch, AskUserQuestion
argument-hint: <problem description>
---

# /evolve-ml - Machine Learning Evolution Subskill (STUB)

This is a **placeholder** for the future ML optimization subskill. It will evolve models for **accuracy, loss minimization, and ML performance metrics**.

**Status**: Not yet implemented. This stub exists to support the master `/evolve` skill's mode detection.

---

## Planned Capabilities

When implemented, this subskill will support:

| Capability | Description |
|------------|-------------|
| Hyperparameter optimization | Evolve learning rates, batch sizes, architectures |
| Architecture search | Evolve neural network layer configurations |
| Feature selection | Evolve optimal feature subsets |
| Loss function design | Evolve custom loss functions |
| Augmentation strategies | Evolve data augmentation pipelines |

---

## Planned Usage

```bash
/evolve-ml <problem description>

# Examples (future)
/evolve-ml improve image classifier accuracy
/evolve-ml optimize hyperparameters for BERT fine-tuning
/evolve-ml find best architecture for time series prediction
```

---

## Current Behavior

If this subskill is invoked, it will:

1. Inform the user that ML mode is not yet implemented
2. Suggest using `/evolve-perf` for performance optimization as an alternative
3. Ask if the user wants to continue with a different mode

```python
def handle_ml_mode_request():
    message = """
    ML evolution mode is not yet implemented.

    Current options:
    1. Use /evolve-perf for runtime performance optimization
    2. Use /evolve-size for code size optimization
    3. Wait for ML mode implementation

    Would you like to proceed with one of the available modes?
    """
    return ask_user_question(message, options=[
        {"label": "Switch to performance mode", "value": "perf"},
        {"label": "Switch to size mode", "value": "size"},
        {"label": "Cancel", "value": "cancel"}
    ])
```

---

## Implementation Roadmap

### Phase 1: Foundation
- [ ] Define ML fitness metrics (accuracy, F1, loss, etc.)
- [ ] Create hyperparameter representation (chromosomes)
- [ ] Implement training evaluation wrapper

### Phase 2: Core Evolution
- [ ] Hyperparameter mutation operators
- [ ] Architecture crossover operators
- [ ] Population selection for ML

### Phase 3: Advanced Features
- [ ] Multi-objective optimization (accuracy vs inference time)
- [ ] Neural architecture search (NAS)
- [ ] AutoML integration

---

## Detection Keywords

The master `/evolve` skill will detect ML mode when requests contain:

| Keyword | Weight |
|---------|--------|
| accuracy | 2 |
| model | 1 |
| train | 1 |
| loss | 2 |
| predict | 2 |
| classify | 2 |
| neural | 2 |
| kaggle | 2 |
| F1 | 2 |
| AUC | 2 |
| epoch | 2 |
| batch size | 2 |
| learning rate | 2 |

---

## File Types That Trigger ML Mode

- `.h5` - Keras models
- `.pkl` - Scikit-learn models
- `.pt`, `.pth` - PyTorch models
- `.onnx` - ONNX models
- Datasets in `data/train/`, `data/test/`

---

## Placeholder Response

When invoked directly:

```
┌─────────────────────────────────────────────────────────────┐
│  /evolve-ml - Not Yet Implemented                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ML evolution mode is coming soon!                          │
│                                                             │
│  Planned features:                                          │
│    • Hyperparameter optimization                            │
│    • Neural architecture search                             │
│    • Feature selection                                      │
│    • Multi-objective optimization                           │
│                                                             │
│  Currently available:                                       │
│    • /evolve-perf  - Runtime performance optimization       │
│    • /evolve-size  - Code/text size minimization            │
│                                                             │
│  Would you like to use one of the available modes?          │
└─────────────────────────────────────────────────────────────┘
```
