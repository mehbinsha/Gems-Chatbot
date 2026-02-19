# backend/nlp/rule_based.py
import json
import random
import re
import os

class ChatbotAssistant:
    def __init__(self, intents_path=None):
        if intents_path is None:
            base = os.path.dirname(__file__)
            intents_path = os.path.join(base, "intents.json")
        with open(intents_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.intents = data.get("intents", [])

        # Build a union set of words for each intent (cleaned)
        self.intent_word_sets = {}
        for intent in self.intents:
            words = set()
            for patt in intent.get("patterns", []):
                toks = self._clean_and_tokenize(patt)
                words.update(toks)
            self.intent_word_sets[intent["tag"]] = words

        # Precompile regex-based routing rules (priority order)
        self.rules = [
            ("goodbye", re.compile(r"\b(bye|goodbye|see you|see ya|i have to go|talk to you later|exit)\b", re.I)),
            ("admission", re.compile(r"\b(admission|apply|apply for|eligib|admission process|how to apply)\b", re.I)),
            ("courses", re.compile(r"\b(course|courses|program|programs|degree|degrees|which course|which courses|what courses|available courses|list of courses)\b", re.I)),
            ("location", re.compile(r"\b(where|location|address|located|campus|how to reach|how to get to|find|direction)\b", re.I)),
            ("contact", re.compile(r"\b(contact|phone|email|call|phone number|contact details|reach out)\b", re.I)),
            ("facilities", re.compile(r"\b(facility|facilities|library|hostel|lab|labs|classroom|canteen|sports)\b", re.I)),
            ("greeting", re.compile(r"\b(hi|hello|hey|good morning|good afternoon|good evening|greetings|is anyone there|what's up|how are you)\b", re.I)),
        ]

    def _clean_and_tokenize(self, text):
        # Lower, remove punctuation, split
        text = (text or "").lower()
        text = re.sub(r"[^\w\s]", " ", text)   # remove punctuation
        tokens = [t for t in text.split() if t.strip()]
        return tokens

    def get_response(self, user_message):
        user_message = (user_message or "").strip()
        if not user_message:
            return "Please type a message."

        cleaned = user_message.lower()

        # 1) Rule-based routing (explicit keywords) - priority
        for tag, pattern in self.rules:
            if pattern.search(cleaned):
                intent = self._find_intent_by_tag(tag)
                if intent:
                    return random.choice(intent.get("responses", []))

        # 2) Word-overlap scoring fallback
        user_tokens = set(self._clean_and_tokenize(user_message))
        best_tag = None
        best_score = 0
        for tag, wordset in self.intent_word_sets.items():
            if not wordset:
                continue
            overlap = len(user_tokens & wordset)
            # normalize by union size to avoid bias to very large intents
            union_size = len(user_tokens | wordset) if (len(user_tokens | wordset) > 0) else 1
            score = overlap / union_size
            if score > best_score:
                best_score = score
                best_tag = tag

        # require at least one overlapping token to accept intent
        if best_tag and best_score > 0.0:
            intent = self._find_intent_by_tag(best_tag)
            if intent:
                return random.choice(intent.get("responses", []))

        # final fallback
        fallback_intent = self._find_intent_by_tag("fallback")
        if fallback_intent:
            return random.choice(fallback_intent.get("responses", []))
        return "I'm sorry, I didn't catch that. Could you rephrase?"

    def _find_intent_by_tag(self, tag):
        for intent in self.intents:
            if intent.get("tag") == tag:
                return intent
        return None
