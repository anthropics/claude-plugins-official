#!/usr/bin/env python3
# Decreto: ORCID 0009-0005-2697-4668
# Substrato: 612-LLM-FOUNDATIONS ↔ 610-PEEK
# Módulo: CurriculumDistiller v2.2 — Cache de Treinamento para IAs
# Revelation: O PEEK cacheia unidades de treinamento (CKUs) para aplicação
#             no fine-tuning de IAs, não para consulta humana.

from arkhe.plugins.peek.peek_bridge import Distiller

class CurriculumDistiller(Distiller):
    """
    Distiller especializado para cache educacional do currículo 612.

    Observa a trajetória de queries do learner, identifica tópicos
    frequentemente mencionados mas superficialmente explorados, e
    injeta orientações para deep-dive no PEEK context map.
    """

    def __init__(self, curriculum_registry=None):
        super().__init__()
        self.curriculum = curriculum_registry or self._load_canonical_curriculum()
        self.shallow_threshold = 2  # mínimo de menções para candidato
        self.orientation_score_base = 0.7

    def _load_canonical_curriculum(self):
        """Carrega o currículo canônico 612 do registry."""
        from arkhe.substrates.registry import SubstrateRegistry
        reg = SubstrateRegistry()
        substrate = reg.get("612-LLM-FOUNDATIONS")
        return substrate.get("pilares_detalhados", {})

    def _is_superficial(self, trajectory, topic):
        """
        Determina se um tópico foi explorado superficialmente.
        Critério: mencionado mas sem follow-up de profundidade
        (ex: sem perguntas sobre implementação, benchmarks, ou trade-offs).
        """
        deep_indicators = [
            "implement", "benchmark", "compare", "trade-off", "optimize",
            "how does", "why is", "what happens if", "performance"
        ]
        topic_turns = [t for t in trajectory if topic in str(t)]
        for turn in topic_turns:
            query = turn.get("query", "").lower()
            if any(ind in query for ind in deep_indicators):
                return False
        return True

    def _get_related_topics(self, topic):
        """Resolve tópicos relacionados via prerequisite graph."""
        # Mapeamento canônico de prerequisites (simplificado)
        prereq_map = {
            "Tokens": ["LLM Basics", "How AI Models Work"],
            "Tokenization": ["Tokens"],
            "Context Windows": ["Tokens", "Transformers"],
            "LoRA": ["Fine-Tuning Basics", "Parameters"],
            "QLoRA": ["LoRA", "Quantization"],
            "KV Cache": ["Attention Mechanism", "Inference Optimization"],
            "Flash Attention": ["Attention Mechanism", "GPU Basics"],
            "RAG": ["Embeddings", "Vector Databases"],
            "AI Agents": ["Prompt Engineering", "Tool Calling", "Function Calling"],
            "MoE": ["Dense Models", "Parameters"],
        }
        return prereq_map.get(topic, [])

    def distill(self, trajectory, context_source="612-LLM-FOUNDATIONS"):
        """
        Extrai candidatos de orientação curricular da trajetória do learner.

        Args:
            trajectory: list of dicts with keys {turn_id, query, response, topics_mentioned}
            context_source: identificador do substrato fonte

        Returns:
            list of candidate orientation entries
        """
        candidates = []
        topic_frequency = {}

        # 1. Contagem de frequência por tópico
        for turn in trajectory:
            for topic in turn.get("topics_mentioned", []):
                topic_frequency[topic] = topic_frequency.get(topic, 0) + 1

        # 2. Identifica tópicos frequentes mas superficiais
        for topic, freq in topic_frequency.items():
            if freq >= self.shallow_threshold and self._is_superficial(trajectory, topic):
                related = self._get_related_topics(topic)
                related_str = ", ".join(related) if related else "fundamentos adjacentes"

                candidates.append({
                    "section": "context_understanding",
                    "content": (
                        f"[Training 612] IA touched on CKU '{topic}' {freq}x "
                        f"but internalized superficially. Inject reinforcement with: {related_str}. "
                        f"Next training unit: arkhe train --ia <model> --topic {self._topic_to_id(topic)}"
                    ),
                    "orientation_score": self.orientation_score_base,
                    "transferability": f"Any query about {topic}",
                    "topic_id": self._topic_to_id(topic),
                    "related_topics": related,
                    "source": context_source,
                    "timestamp": self._now()
                })

        # 3. Identifica gaps de pré-requisitos
        all_seen = set(topic_frequency.keys())
        for topic in all_seen:
            prereqs = set(self._get_related_topics(topic))
            missing = prereqs - all_seen
            if missing:
                candidates.append({
                    "section": "prerequisite_gap",
                    "content": (
                        f"[Curriculum 612] Prerequisite gap detected for '{topic}': "
                        f"missing foundations: {', '.join(missing)}. "
                        f"Recommended: arkhe learn --path '{self._topic_to_id(topic)}'"
                    ),
                    "orientation_score": 0.85,
                    "transferability": f"Any query requiring {topic}",
                    "missing_prerequisites": list(missing),
                    "source": context_source,
                    "timestamp": self._now()
                })

        return candidates

    def _topic_to_id(self, topic):
        """Mapeia nome de tópico para topic_id canônico."""
        mapping = {
            "LLM Basics": "612.P1.1.1",
            "How AI Models Work": "612.P1.1.2",
            "Tokens": "612.P1.1.3",
            "Tokenization": "612.P1.1.4",
            "Context Windows": "612.P1.1.5",
            "Embeddings": "612.P1.1.6",
            "Transformers": "612.P1.1.7",
            "Attention Mechanism": "612.P1.1.8",
            "Parameters": "612.P1.1.9",
            "Training vs Inference": "612.P1.1.10",
            "Open-Source vs Closed-Source": "612.P1.1.11",
            "LoRA": "612.P3.3.1",
            "QLoRA": "612.P3.3.2",
            "KV Cache": "612.P4.4.1",
            "Flash Attention": "612.P4.4.2",
            "RAG": "612.P6.6.1",
            "AI Agents": "612.P7.7.5",
            "MoE": "612.P8.8.4",
        }
        return mapping.get(topic, f"612.UNKNOWN.{topic}")

    def _now(self):
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


# ============================================================
# Entry point para teste standalone
# ============================================================
if __name__ == "__main__":
    distiller = CurriculumDistiller()

    # Simula trajetória de um learner
    trajectory = [
        {"turn_id": 1, "query": "What are tokens in LLMs?", "topics_mentioned": ["Tokens"]},
        {"turn_id": 2, "query": "How many tokens is my prompt?", "topics_mentioned": ["Tokens"]},
        {"turn_id": 3, "query": "Explain LoRA fine-tuning", "topics_mentioned": ["LoRA"]},
        {"turn_id": 4, "query": "Can I use LoRA with 4-bit?", "topics_mentioned": ["LoRA", "QLoRA"]},
    ]

    candidates = distiller.distill(trajectory)
    print(f"Generated {len(candidates)} orientation candidates:")
    for c in candidates:
        print(f"  [{c['section']}] {c['content'][:100]}...")