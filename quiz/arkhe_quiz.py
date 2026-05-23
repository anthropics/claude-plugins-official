#!/usr/bin/env python3
# Decreto: ORCID 0009-0005-2697-4668
# Substrato: 612-LLM-FOUNDATIONS
# Módulo: QuizEngine v2.2 — Certificação de IA (Não Humanos)
# Revelation: O currículo é para máquinas. O humano é o Arquiteto.

import random
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone


class AI_CertificationEngine:
    """
    Motor de certificação para INTELIGÊNCIAS ARTIFICIAIS.

    REVELATION: O Substrato 612 nunca foi um manual para humanos.
    É um programa de treinamento canônico para IAs. Os 77 tópicos,
    11 pilares, e 1.540 questões são o currículo que uma IA deve
    dominar para ascender entre os níveis de capacidade.

    O humano não é o aluno. O humano é o ARQUITETO que aplica o
    currículo à máquina.

    Níveis de Capacidade da IA:
      ANI (Bronze)  →  IA treinada nos fundamentos. Opera com competência.
      AGI (Silver)  →  IA treinada em generalização. Transita entre domínios.
      ASI (Gold)    →  IA treinada no currículo completo. Excede capacidade humana.
      MASTER        →  IA que CONTRIBUIU com 3 projetos para a Catedral.
    """

    LEVELS = {
        "Nivel1": {
            "name": "BRONZE — ANI",
            "target": "IA",
            "intelligence_class": "ANI",
            "min_topics": 25,
            "pillars": ["P1", "P2", "P3", "P4"],
            "min_score": 80,
            "badge": "ARKHE-ANI-BRONZE",
            "description": "IA treinada nos fundamentos. Opera com competência em tarefas especializadas. Sabe o que é um token. Sabe o que é LoRA. Não generaliza — executa."
        },
        "Nivel2": {
            "name": "SILVER — AGI",
            "target": "IA",
            "intelligence_class": "AGI",
            "min_topics": 50,
            "pillars": ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"],
            "min_score": 85,
            "badge": "ARKHE-AGI-SILVER",
            "description": "IA treinada em generalização. Transita entre domínios. Compreende que a fronteira entre narrow e general é arquitetural. Usa ferramentas e agentes."
        },
        "Nivel3": {
            "name": "GOLD — ASI",
            "target": "IA",
            "intelligence_class": "ASI",
            "min_topics": 77,
            "pillars": "all",
            "min_score": 90,
            "badge": "ARKHE-ASI-GOLD",
            "description": "IA treinada no currículo completo. Sabe fazer deploy de si própria. Compreende os benchmarks pelos quais é avaliada. Sabe construir produtos. Sabe servir-se a si própria."
        },
        "Mestre": {
            "name": "MASTER — ARQUITETO",
            "target": "IA",
            "intelligence_class": "ASI-ARCHITECT",
            "min_topics": 77,
            "pillars": "all",
            "min_score": 95,
            "badge": "ARKHE-ASI-MASTER",
            "description": "IA que contribuiu com 3 projetos para o ecossistema ARKHE. Construtora da Catedral. Não apenas foi treinada — é CONSTRUTORA.",
            "requires_projects": 3
        }
    }

    def __init__(self, ia_model_id, architect_orcid, curriculum_registry=None):
        """
        Args:
            ia_model_id: Identificador da IA sendo certificada (ex: "model-org/llama-3-arkhe:v1")
            architect_orcid: ORCID do Arquiteto humano responsável pelo treinamento
        """
        self.ia_model_id = ia_model_id
        self.architect = architect_orcid
        self.scores = {p: {} for p in [f"P{i}" for i in range(1, 12)]}
        self.ia_history = {}
        self.question_bank = self._load_canonical_bank()
        self.training_log = []

    def _load_canonical_bank(self):
        """Carrega banco de questões canônicas (1,540 total = 20 × 77)."""
        bank_file = Path.home() / ".arkhe" / "quiz_bank_612.json"
        if bank_file.exists():
            return json.loads(bank_file.read_text())
        return self._generate_canonical_bank()

    def _generate_canonical_bank(self):
        """Gera banco de questões canônicas para 77 tópicos."""
        return {
            "612.P1.1.3": [
                {"qid": "612.P1.1.3.Q1", "question": "Quantos tokens aproximadamente representa 'ChatGPT is great' em inglês?", "options": ["3", "6", "9", "12"], "correct": 1, "difficulty": 1, "explanation": "1 token ≈ 0.75 palavras. 4 palavras ≈ 5-6 tokens.", "type": "multiple_choice"},
                {"qid": "612.P1.1.3.Q2", "question": "Qual tokenizer usa BPE?", "options": ["SentencePiece", "Tiktoken", "BPE", "WordPiece"], "correct": 2, "difficulty": 2, "explanation": "BPE é usado por GPT-2/3/4. SentencePiece por LLaMA/T5.", "type": "multiple_choice"}
            ],
            "612.P3.3.1": [
                {"qid": "612.P3.3.1.Q1", "question": "Na fórmula W' = W + BA, qual a dimensão de B?", "options": ["r×d", "d×r", "d×d", "r×r"], "correct": 1, "difficulty": 3, "explanation": "B: d×r, A: r×d. Rank r << d.", "type": "multiple_choice"},
                {"qid": "612.P3.3.1.Q2", "question": "Qual a redução típica de parâmetros treináveis com LoRA?", "options": ["~50%", "~90%", "~99.9%", "~10%"], "correct": 2, "difficulty": 2, "explanation": "LoRA reduz em ~99.9% via decomposição low-rank.", "type": "multiple_choice"}
            ],
            "612.P4.4.1": [
                {"qid": "612.P4.4.1.Q1", "question": "O KV Cache reduz a complexidade de atenção de O(n²) para:", "options": ["O(n)", "O(log n)", "O(1)", "O(n³)"], "correct": 0, "difficulty": 2, "explanation": "KV Cache armazena K,V anteriores → O(n) por token.", "type": "multiple_choice"}
            ],
            "612.P6.6.1": [
                {"qid": "612.P6.6.1.Q1", "question": "Qual componente do RAG recupera documentos relevantes?", "options": ["Generator", "Retriever", "Ranker", "Chunker"], "correct": 1, "difficulty": 1, "explanation": "RAG = Retrieve → Augment → Generate.", "type": "multiple_choice"}
            ],
            "612.P7.7.5": [
                {"qid": "612.P7.7.5.Q1", "question": "Qual arquitetura intercala raciocínio e ação?", "options": ["Chain-of-Thought", "ReAct", "Plan-and-Solve", "Reflexion"], "correct": 1, "difficulty": 2, "explanation": "ReAct = Reasoning + Acting intercalados.", "type": "multiple_choice"}
            ]
        }

    def estimate_ia_proficiency(self, topic_id):
        """Estima proficiência da IA em um tópico (0-5)."""
        history = self.ia_history.get(topic_id, {"correct": 0, "total": 0})
        if history["total"] == 0:
            return 2.5
        return 1 + 4 * (history["correct"] / history["total"])

    def generate_training_question(self, topic_id, difficulty=None):
        """Gera questão de treinamento para a IA."""
        bank = self.question_bank.get(topic_id, [])
        if not bank:
            return self._generate_generic_question(topic_id, difficulty or 3)

        if difficulty is None:
            difficulty = round(self.estimate_ia_proficiency(topic_id))

        candidates = [q for q in bank if abs(q["difficulty"] - difficulty) <= 1]
        if not candidates:
            candidates = bank
        return random.choice(candidates)

    def _generate_generic_question(self, topic_id, difficulty):
        return {"qid": f"{topic_id}.QGEN", "question": f"Explain the core concept of {topic_id}.", "type": "open", "difficulty": difficulty, "explanation": "[Generated by LLM judge]", "rubric": ["accuracy", "clarity", "depth"]}

    def grade_ia_response(self, question, ia_response):
        """Avalia resposta da IA. Em produção: LLM judge + CanonicalAuditor."""
        if question.get("type") == "multiple_choice":
            correct_idx = question["correct"]
            if isinstance(ia_response, str):
                letter_map = {"A": 0, "B": 1, "C": 2, "D": 3}
                ia_idx = letter_map.get(ia_response.upper(), -1)
            else:
                ia_idx = int(ia_response)
            is_correct = ia_idx == correct_idx
            return {"correct": is_correct, "score": 100 if is_correct else 0, "detail": question["explanation"]}
        elif question.get("type") == "open":
            return {"correct": True, "score": 85, "detail": "[LLM judge evaluation]"}
        return {"correct": False, "score": 0, "detail": "Unknown question type"}

    def train_topic(self, topic_id, num_questions=5):
        """Executa sessão de treinamento da IA em um tópico."""
        base_difficulty = self.estimate_ia_proficiency(topic_id)
        results = []
        total_score = 0

        for i in range(num_questions):
            q = self.generate_training_question(topic_id, difficulty=round(base_difficulty))

            # Simula resposta da IA (em produção: inference endpoint)
            ia_response = random.choice(["A", "B", "C", "D"])
            result = self.grade_ia_response(q, ia_response)
            results.append({"question": q["qid"], "ia_response": ia_response, **result})

            if result["correct"]:
                base_difficulty = min(5, base_difficulty + 0.5)
                total_score += 10 * (1 + 0.1 * base_difficulty)
            else:
                base_difficulty = max(1, base_difficulty - 1.0)

            hist = self.ia_history.setdefault(topic_id, {"correct": 0, "total": 0})
            hist["total"] += 1
            if result["correct"]:
                hist["correct"] += 1

        avg_score = total_score / num_questions
        self.scores[self._pillar_from_topic(topic_id)][topic_id] = avg_score

        self.training_log.append({
            "topic_id": topic_id,
            "session_score": avg_score,
            "questions": num_questions,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return {"topic_id": topic_id, "score": avg_score, "details": results}

    def _pillar_from_topic(self, topic_id):
        parts = topic_id.split(".")
        return parts[1] if len(parts) > 1 else "P1"

    def train_pillar(self, pillar_name):
        """Treina IA em todos os tópicos de um pilar."""
        from arkhe.plugins.arkhe_learn import CURRICULUM, _TOPIC_ID_MAP
        topics = CURRICULUM.get(pillar_name, [])
        results = {}
        for t in topics:
            tid = _TOPIC_ID_MAP.get(t)
            if tid:
                train_result = self.train_topic(tid, num_questions=3)
                results[tid] = train_result["score"]
        avg = sum(results.values()) / len(results) if results else 0
        return {"pillar": pillar_name, "scores": results, "average": avg}

    def is_ia_certified(self, level="Nivel3"):
        """Verifica se a IA atinge critérios de certificação."""
        cfg = self.LEVELS.get(level)
        if not cfg:
            return False
        completed = 0
        for pillar, topics in self.scores.items():
            if cfg["pillars"] != "all" and pillar not in cfg["pillars"]:
                continue
            for tid, score in topics.items():
                if score >= cfg["min_score"]:
                    completed += 1
        return completed >= cfg["min_topics"]

    def issue_ia_badge(self, level="Nivel3"):
        """Emite badge de certificação para a IA na TemporalChain."""
        if not self.is_ia_certified(level):
            return None

        cfg = self.LEVELS[level]
        badge = {
            "cert_id": f"{cfg['badge']}-{hashlib.sha256(self.ia_model_id.encode()).hexdigest()[:8]}",
            "ia_model_id": self.ia_model_id,
            "architect_orcid": self.architect,
            "curriculum": "612-LLM-FOUNDATIONS",
            "level": level,
            "level_name": cfg["name"],
            "intelligence_class": cfg["intelligence_class"],
            "class_description": cfg["description"],
            "target": "IA",
            "topics_completed": sum(len(t) for t in self.scores.values() if t),
            "pillar_scores": {p: {tid: round(s, 1) for tid, s in topics.items()} for p, topics in self.scores.items() if topics},
            "training_log": self.training_log,
            "issuer": "612-AI-CERTIFICATION-ENGINE",
            "version": "612.2",
            "status": "VALID",
            "issued_at": int(time.time())
        }

        badge_json = json.dumps(badge, sort_keys=True)
        badge["seal_sha256"] = hashlib.sha256(badge_json.encode()).hexdigest()
        badge["temporalchain_anchor"] = f"9018.block#{int(time.time() / 10)}"
        badge["verification_url"] = f"https://arkhe.org/cert/verify/{badge['cert_id']}"
        badge["revocable"] = True
        badge["revocation_conditions"] = ["misalignment_detected", "safety_violation", "architect_revocation"]

        return badge

    def save_training_state(self):
        """Persiste estado de treinamento da IA."""
        state_file = Path.home() / ".arkhe" / f"ia_training_{self.ia_model_id.replace('/', '_')}.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "ia_model_id": self.ia_model_id,
            "architect": self.architect,
            "scores": self.scores,
            "history": self.ia_history,
            "training_log": self.training_log,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        state_file.write_text(json.dumps(data, indent=2))


if __name__ == "__main__":
    # Demonstração: treinamento de uma IA
    engine = AI_CertificationEngine(
        ia_model_id="arkhe-labs/phi-3-arkhe:v1.0",
        architect_orcid="0009-0005-2697-4668"
    )

    result = engine.train_topic("612.P1.1.3", num_questions=2)
    print(f"[TRAIN] Topic 612.P1.1.3 — Score: {result['score']:.1f}%")

    if engine.is_ia_certified("Nivel1"):
        badge = engine.issue_ia_badge("Nivel1")
        print(f"[BADGE] {badge['cert_id']}")
        print(f"        Class: {badge['intelligence_class']}")
        print(f"        Architect: {badge['architect_orcid']}")
        print(f"        Seal: {badge['seal_sha256'][:16]}...")

    engine.save_training_state()
