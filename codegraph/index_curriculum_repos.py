#!/usr/bin/env python3
# Decreto: ORCID 0009-0005-2697-4668
# Substrato: 612-LLM-FOUNDATIONS ↔ 611-CODEGRAPH
# Módulo: RepoIndexer v2.2 — Indexação de Repositórios de Treinamento para IAs
# Revelation: Cada repositório indexado é um dataset de treinamento prático
#             que a IA deve estudar para internalizar o conceito.

import os
import subprocess
import json
import hashlib
from pathlib import Path

# ============================================================
# MAPEAMENTO CANÔNICO: Tópico → Repositórios Exemplares
# ============================================================
REPO_MAP = {
    # P1 — FOUNDATIONS
    "612.P1.1.4": ["https://github.com/openai/tiktoken", "https://github.com/huggingface/tokenizers", "https://github.com/google/sentencepiece"],
    "612.P1.1.7": ["https://github.com/huggingface/transformers", "https://github.com/pytorch/pytorch"],
    "612.P1.1.8": ["https://github.com/Dao-AILab/flash-attention", "https://github.com/huggingface/transformers"],

    # P2 — DATASETS & TRAINING
    "612.P2.2.1": ["https://github.com/tatsu-lab/stanford_alpaca", "https://github.com/databrickslabs/dolly"],
    "612.P2.2.3": ["https://github.com/anthropics/hh-rlhf", "https://github.com/stanfordnlp/SHP"],
    "612.P2.2.4": ["https://github.com/tatsu-lab/stanford_alpaca", "https://github.com/nlpxucan/WizardLM"],

    # P3 — FINE-TUNING
    "612.P3.3.1": ["https://github.com/huggingface/peft", "https://github.com/microsoft/LoRA", "https://github.com/tloen/alpaca-lora"],
    "612.P3.3.2": ["https://github.com/artidoro/qlora", "https://github.com/huggingface/peft"],
    "612.P3.3.3": ["https://github.com/huggingface/trl", "https://github.com/rasbt/LLMs-from-scratch"],
    "612.P3.3.4": ["https://github.com/huggingface/trl", "https://github.com/openai/instructgpt"],
    "612.P3.3.5": ["https://github.com/ggerganov/llama.cpp", "https://github.com/AutoGPTQ/AutoGPTQ"],
    "612.P3.3.8": ["https://github.com/ggerganov/llama.cpp"],

    # P4 — INFERENCE & OPTIMIZATION
    "612.P4.4.1": ["https://github.com/vllm-project/vllm", "https://github.com/ggerganov/llama.cpp", "https://github.com/huggingface/transformers"],
    "612.P4.4.2": ["https://github.com/Dao-AILab/flash-attention", "https://github.com/vllm-project/vllm"],
    "612.P4.4.3": ["https://github.com/vllm-project/vllm", "https://github.com/FasterDecoding/Medusa"],
    "612.P4.4.5": ["https://github.com/vllm-project/vllm", "https://github.com/huggingface/text-generation-inference", "https://github.com/SGLang/sglang"],

    # P5 — LOCAL AI ECOSYSTEM
    "612.P5.5.1": ["https://github.com/ggerganov/llama.cpp"],
    "612.P5.5.2": ["https://github.com/ollama/ollama", "https://github.com/jmorganca/ollama"],
    "612.P5.5.3": ["https://github.com/vllm-project/vllm"],
    "612.P5.5.4": ["https://github.com/ml-explore/mlx"],
    "612.P5.5.5": ["https://github.com/huggingface/transformers", "https://github.com/huggingface/datasets"],
    "612.P5.5.6": ["https://github.com/unslothai/unsloth"],
    "612.P5.5.7": ["https://github.com/OpenAccess-AI-Collective/axolotl"],
    "612.P5.5.8": ["https://github.com/huggingface/peft"],
    "612.P5.5.9": ["https://github.com/huggingface/trl"],

    # P6 — RAG & MEMORY
    "612.P6.6.1": ["https://github.com/langchain-ai/langchain", "https://github.com/run-llama/llama_index", "https://github.com/chroma-core/chroma"],
    "612.P6.6.2": ["https://github.com/facebookresearch/faiss", "https://github.com/qdrant/qdrant", "https://github.com/chroma-core/chroma"],
    "612.P6.6.6": ["https://github.com/facebookresearch/faiss", "https://github.com/chroma-core/chroma"],

    # P7 — AGENTS & WORKFLOWS
    "612.P7.7.5": ["https://github.com/Significant-Gravitas/AutoGPT", "https://github.com/joaomdmoura/crewAI", "https://github.com/microsoft/autogen"],
    "612.P7.7.7": ["https://github.com/joaomdmoura/crewAI", "https://github.com/microsoft/autogen", "https://github.com/geekan/MetaGPT"],
    "612.P7.7.8": ["https://github.com/ServiceNow/BrowserGym", "https://github.com/web-arena-x/webarena"],

    # P8 — MODEL TYPES
    "612.P8.8.1": ["https://github.com/openai/CLIP", "https://github.com/haotian-liu/LLaVA"],
    "612.P8.8.4": ["https://github.com/mistralai/mistral-src", "https://github.com/deepseek-ai/DeepSeek-V2"],
    "612.P8.8.5": ["https://github.com/meta-llama/codellama", "https://github.com/bigcode-project/starcoder"],
    "612.P8.8.6": ["https://github.com/deepseek-ai/DeepSeek-R1"],

    # P9 — DEPLOYMENT
    "612.P9.9.3": ["https://github.com/vllm-project/vllm", "https://github.com/SGLang/sglang", "https://github.com/NVIDIA/TensorRT-LLM"],
    "612.P9.9.4": ["https://github.com/vllm-project/vllm", "https://github.com/huggingface/text-generation-inference"],

    # P10 — EVALUATION
    "612.P10.10.1": ["https://github.com/EleutherAI/lm-evaluation-harness", "https://github.com/openai/simple-evals"],

    # P11 — REAL-WORLD SKILLS
    "612.P11.11.2": ["https://github.com/github/copilot.vim", "https://github.com/sourcegraph/cody", "https://github.com/continuedev/continue"],
}

BASE_DIR = Path.home() / ".arkhe" / "curriculum-repos"
IPFS_PIN = True  # Flag para pinning IPFS


class CurriculumRepoIndexer:
    """
    Indexa repositórios de exemplo para cada tópico do currículo 612
    usando CodeGraph (611). Armazena índices no IPFS e registra no PEEK.
    """

    def __init__(self, base_dir=BASE_DIR, repo_map=REPO_MAP):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.repo_map = repo_map
        self.index_log = []

    def clone_and_index(self, topic_id, repo_url, force=False):
        """Clona repo, inicializa CodeGraph, e retorna CID do índice."""
        repo_name = repo_url.rstrip("/").split("/")[-1]
        target_dir = self.base_dir / topic_id / repo_name
        codegraph_dir = target_dir / ".codegraph"

        # Clone (shallow)
        if not target_dir.exists() or force:
            print(f"[612↔611] Cloning {repo_name} for {topic_id}...")
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
                capture_output=True, check=False
            )

        # Initialize CodeGraph
        if not codegraph_dir.exists() or force:
            print(f"[612↔611] Indexing training repos with CodeGraph: {repo_name}")
            try:
                subprocess.run(
                    ["codegraph", "init", str(target_dir)],
                    capture_output=True, check=False
                )
            except FileNotFoundError:
                print(f"  ⚠ codegraph CLI not found. Skipping AST index.")
                # Cria stub mínimo
                codegraph_dir.mkdir(parents=True, exist_ok=True)
                (codegraph_dir / "index.json").write_text(json.dumps({
                    "repo": repo_name,
                    "topic_id": topic_id,
                    "url": repo_url,
                    "indexed_at": self._now(),
                    "status": "stub"
                }))

        # Store on IPFS
        cid = None
        if IPFS_PIN and codegraph_dir.exists():
            try:
                result = subprocess.run(
                    ["arkhe", "ipfs", "add", "-r", "-q", str(codegraph_dir)],
                    capture_output=True, text=True, check=False
                )
                cid = result.stdout.strip().split("\n")[-1]
                print(f"  📌 IPFS CID: {cid}")
            except Exception as e:
                print(f"  ⚠ IPFS upload failed: {e}")

        entry = {
            "topic_id": topic_id,
            "repo": repo_name,
            "url": repo_url,
            "local_path": str(target_dir),
            "codegraph_path": str(codegraph_dir),
            "ipfs_cid": cid,
            "indexed_at": self._now()
        }
        self.index_log.append(entry)
        return entry

    def index_all(self, force=False):
        """Indexa todos os repositórios mapeados."""
        total = sum(len(repos) for repos in self.repo_map.values())
        print(f"[612↔611] Indexing training repos {total} repositories across {len(self.repo_map)} topics...")

        for topic_id, repos in self.repo_map.items():
            print(f"\n  Topic: {topic_id}")
            for repo_url in repos:
                self.clone_and_index(topic_id, repo_url, force=force)

        # Save manifest
        manifest = {
            "substrate": "612-LLM-FOUNDATIONS",
            "integration": "611-CODEGRAPH",
            "total_repos": len(self.index_log),
            "total_topics": len(self.repo_map),
            "entries": self.index_log,
            "generated_at": self._now(),
            "seal": self._compute_seal()
        }

        manifest_path = self.base_dir / "codegraph_612_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f"\n✓ Manifest saved: {manifest_path}")
        print(f"  Total indexed: {len(self.index_log)} repos")

        return manifest

    def query_topic(self, topic_id):
        """Retorna repos indexados para um tópico."""
        entries = [e for e in self.index_log if e["topic_id"] == topic_id]
        if not entries:
            # Tenta carregar do manifest
            manifest_path = self.base_dir / "codegraph_612_manifest.json"
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text())
                entries = [e for e in manifest["entries"] if e["topic_id"] == topic_id]
        return entries

    def _now(self):
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    def _compute_seal(self):
        """Computa selo SHA-256 sobre o log de indexação."""
        data = json.dumps(self.index_log, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()


# ============================================================
# CLI Interface
# ============================================================
if __name__ == "__main__":
    import sys

    indexer = CurriculumRepoIndexer()

    if len(sys.argv) > 1 and sys.argv[1] == "--topic":
        topic = sys.argv[2]
        entries = indexer.query_topic(topic)
        print(f"Training repos for CKU {topic}:")
        for e in entries:
            print(f"  • {e['repo']} → {e['url']}")
            if e.get("ipfs_cid"):
                print(f"    IPFS: {e['ipfs_cid']}")
    else:
        manifest = indexer.index_all()
        print(f"\nSeal: {manifest['seal'][:16]}...")
