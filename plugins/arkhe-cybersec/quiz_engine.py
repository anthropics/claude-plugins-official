#!/usr/bin/env python3
"""Quiz engine for cybersecurity certification."""
import random, json, hashlib, time
from .curriculum import CURRICULUM, get_topic

class QuizEngine:
    QUESTION_BANK = {
        "613.P7.1": [
            {"question": "What SQL clause is used to combine results from multiple SELECT statements?",
             "options": {"A": "JOIN", "B": "MERGE", "C": "UNION", "D": "COMBINE"}, "correct": "C",
             "explanation": "UNION combines the result sets of two or more SELECT statements."},
            {"question": "Which character is commonly used to terminate a SQL statement in injection attacks?",
             "options": {"A": "; (semicolon)", "B": "-- (double dash)", "C": "' (single quote)", "D": "# (hash)"}, "correct": "B",
             "explanation": "Double dash (--) is used to comment out the rest of the query in many SQL dialects."},
        ],
        # ... additional question banks for each topic
    }

    def generate_quiz(self, topic_id, count=5):
        topic = get_topic(topic_id)
        if not topic:
            return []
        bank = self.QUESTION_BANK.get(topic_id, [])
        if not bank:
            # Generate synthetic questions
            return self._synthetic_questions(topic, count)
        return random.sample(bank, min(count, len(bank)))

    def _synthetic_questions(self, topic, count):
        return [{
            "question": f"Explain the key concept of {topic['name']}.",
            "options": {"A": "Answer A", "B": "Answer B", "C": "Answer C", "D": "Answer D"},
            "correct": "A",
            "explanation": f"See curriculum topic {topic['id']} for the complete explanation."
        } for _ in range(count)]