import os
import numpy as np
from typing import Optional

# Simple keyword-based medical knowledge base
MEDICAL_KB = [
    {
        "id": "kb001",
        "topic": "Common Cold",
        "content": "The common cold is a viral infection of the upper respiratory tract. Symptoms include runny nose, sneezing, sore throat, cough, and mild fever. Treatment focuses on rest, hydration, and over-the-counter medications. Most cases resolve within 7-10 days.",
        "keywords": ["cold", "runny nose", "sneeze", "sore throat", "cough", "fever"],
    },
    {
        "id": "kb002",
        "topic": "Influenza",
        "content": "Influenza (flu) is a contagious respiratory illness caused by influenza viruses. Symptoms include high fever, body aches, fatigue, dry cough, and headache. Antiviral medications may help if started early. Annual vaccination is recommended for prevention.",
        "keywords": ["flu", "fever", "body aches", "fatigue", "cough", "headache"],
    },
    {
        "id": "kb003",
        "topic": "Hypertension",
        "content": "Hypertension (high blood pressure) is a condition where blood pressure consistently reads 130/80 mmHg or higher. Often asymptomatic. Risk factors include age, obesity, high salt intake, and family history. Management includes lifestyle changes and medications like ACE inhibitors.",
        "keywords": ["high blood pressure", "hypertension", "blood pressure", "headache", "dizziness"],
    },
    {
        "id": "kb004",
        "topic": "Type 2 Diabetes",
        "content": "Type 2 diabetes is a metabolic disorder characterized by insulin resistance. Symptoms include increased thirst, frequent urination, fatigue, blurred vision, and slow wound healing. Management involves diet, exercise, glucose monitoring, and medications like metformin.",
        "keywords": ["diabetes", "thirst", "frequent urination", "fatigue", "blurred vision", "sugar"],
    },
    {
        "id": "kb005",
        "topic": "Migraine",
        "content": "Migraine is a neurological condition causing intense headaches, often with nausea, vomiting, and sensitivity to light and sound. Triggers include stress, certain foods, hormonal changes, and sleep disruption. Treatment includes pain relievers, triptans, and preventive medications.",
        "keywords": ["migraine", "headache", "nausea", "light sensitivity", "sound sensitivity", "aura"],
    },
    {
        "id": "kb006",
        "topic": "Gastroenteritis",
        "content": "Gastroenteritis is inflammation of the stomach and intestines, usually from viral or bacterial infection. Symptoms include diarrhea, vomiting, abdominal cramps, and nausea. Treatment focuses on rehydration and electrolyte replacement. Most cases resolve within a few days.",
        "keywords": ["stomach", "diarrhea", "vomiting", "nausea", "abdominal pain", "cramps"],
    },
    {
        "id": "kb007",
        "topic": "Pneumonia",
        "content": "Pneumonia is a lung infection causing inflammation in air sacs. Symptoms include productive cough, fever, chills, shortness of breath, and chest pain. Bacterial pneumonia is treated with antibiotics. Viral pneumonia requires supportive care. Seek emergency care for breathing difficulty.",
        "keywords": ["pneumonia", "cough", "fever", "shortness of breath", "chest pain", "chills"],
    },
    {
        "id": "kb008",
        "topic": "Asthma",
        "content": "Asthma is a chronic respiratory condition with airway inflammation. Symptoms include wheezing, shortness of breath, chest tightness, and coughing, especially at night or during exercise. Management includes inhaled bronchodilators and corticosteroids. Avoid known triggers.",
        "keywords": ["asthma", "wheezing", "shortness of breath", "chest tightness", "cough", "allergy"],
    },
    {
        "id": "kb009",
        "topic": "Anxiety Disorders",
        "content": "Anxiety disorders involve excessive worry and fear. Physical symptoms include rapid heartbeat, sweating, trembling, fatigue, and sleep disturbance. Treatment combines psychotherapy (CBT) and medications (SSRIs). Lifestyle modifications like exercise and meditation help manage symptoms.",
        "keywords": ["anxiety", "worry", "rapid heartbeat", "sweating", "trembling", "sleep", "panic"],
    },
    {
        "id": "kb010",
        "topic": "COVID-19",
        "content": "COVID-19 is caused by SARS-CoV-2 virus. Symptoms range from mild (fever, cough, fatigue, loss of taste/smell) to severe (difficulty breathing, chest pain). Prevention includes vaccination, masking, and ventilation. High-risk patients may qualify for antiviral treatment (Paxlovid).",
        "keywords": ["covid", "coronavirus", "fever", "cough", "fatigue", "loss of smell", "loss of taste"],
    },
    {
        "id": "kb011",
        "topic": "Anemia",
        "content": "Anemia is a condition with insufficient healthy red blood cells. Common type is iron-deficiency anemia. Symptoms include fatigue, weakness, pale skin, shortness of breath, dizziness, and cold hands/feet. Treatment depends on cause: iron supplements, B12, or addressing underlying conditions.",
        "keywords": ["anemia", "fatigue", "weakness", "pale", "dizziness", "shortness of breath"],
    },
    {
        "id": "kb012",
        "topic": "Skin Allergy / Eczema",
        "content": "Eczema (atopic dermatitis) causes red, itchy, inflamed skin. Triggers include allergens, irritants, stress, and weather changes. Management includes moisturizers, topical corticosteroids, and avoiding triggers. Severe cases may require immunomodulators or phototherapy.",
        "keywords": ["rash", "itchy", "skin", "eczema", "allergy", "redness", "dry skin"],
    },
]


class MedicalRetriever:
    def __init__(self):
        self.documents = MEDICAL_KB
        # Build a simple keyword index
        self.keyword_index: dict[str, list[int]] = {}
        for i, doc in enumerate(self.documents):
            for kw in doc.get("keywords", []):
                kw_lower = kw.lower()
                if kw_lower not in self.keyword_index:
                    self.keyword_index[kw_lower] = []
                self.keyword_index[kw_lower].append(i)

    def _score_document(self, doc: dict, query: str) -> float:
        query_lower = query.lower()
        score = 0.0
        for kw in doc.get("keywords", []):
            if kw.lower() in query_lower:
                score += 1.0
        if doc["topic"].lower() in query_lower:
            score += 2.0
        content_matches = sum(1 for word in query_lower.split() if word in doc["content"].lower())
        score += content_matches * 0.3
        return score

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        scores = [(i, self._score_document(doc, query)) for i, doc in enumerate(self.documents)]
        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in scores[:top_k]:
            if score > 0:
                doc = self.documents[idx]
                results.append({
                    "content": doc["content"],
                    "source": doc["topic"],
                    "relevance": min(score / 5.0, 0.99),
                })
        return results

    def get_context(self, query: str, top_k: int = 3) -> str:
        docs = self.retrieve(query, top_k)
        if not docs:
            return ""
        parts = ["[Medical Knowledge Base References]"]
        for i, doc in enumerate(docs):
            parts.append(f"\nReference {i+1} ({doc['source']}, relevance: {doc['relevance']:.2f}):\n{doc['content']}")
        return "\n".join(parts)


retriever = MedicalRetriever()
