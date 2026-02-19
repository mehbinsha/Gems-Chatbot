# backend/nlp/ml_engine.py
import os
import json
import random
import torch
import numpy as np

from backend.nlp.rule_based import ChatbotAssistant as RuleAssistant

# Minimal model class that mirrors the training architecture
import torch.nn as nn

class ChatbotModel(nn.Module):
    def __init__(self, input_size, output_size):
        super(ChatbotModel, self).__init__()
        self.fc1 = nn.Linear(input_size, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, output_size)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.5)

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return x

class ChatbotML:
    def __init__(self, model_path, dims_path, intents_path):
        # validate files
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
        if not os.path.exists(dims_path):
            raise FileNotFoundError(f"Dimensions file not found at {dims_path}")
        if not os.path.exists(intents_path):
            raise FileNotFoundError(f"Intents file not found at {intents_path}")

        with open(dims_path, "r") as f:
            dims = json.load(f)
        self.input_size = dims["input_size"]
        self.output_size = dims["output_size"]

        # load intents + responses and vocabulary via the rule assistant parsing approach
        # We'll reuse the rule-based parser to build vocabulary/documents for consistency
        self.rule_assistant = RuleAssistant(intents_path)
        # train/prepare details were in your training script; we expect rule_assistant to have intent_word_sets,
        # but ML requires exact vocabulary; for simplicity we create a 'vocabulary' from rule_assistant sets
        vocab = set()
        for s in self.rule_assistant.intent_word_sets.values():
            vocab.update(s)
        self.vocabulary = sorted(vocab)

        # initialize and load model
        self.model = ChatbotModel(self.input_size, self.output_size)
        self.model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
        self.model.eval()

        # keep a map of intents (order matters)
        self.intents = [intent.get("tag") for intent in self.rule_assistant.intents]
        self.intents_responses = {intent.get("tag"): intent.get("responses") for intent in self.rule_assistant.intents}

    def _clean_and_tokenize(self, text):
        import re
        text = (text or "").lower()
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = [t for t in text.split() if t.strip()]
        return tokens

    def _bag_of_words(self, words):
        return [1 if w in words else 0 for w in self.vocabulary]

    def get_response(self, user_message):
        user_message = (user_message or "").strip()
        if not user_message:
            return "Please type a message."
        words = self._clean_and_tokenize(user_message)
        bag = self._bag_of_words(words)
        import torch
        with torch.no_grad():
            inputs = torch.tensor([bag], dtype=torch.float32)
            outputs = self.model(inputs)
            predicted_index = torch.argmax(outputs, dim=1).item()
            if predicted_index < 0 or predicted_index >= len(self.intents):
                # fallback to rule-based
                return random.choice(self.intents_responses.get("fallback", ["I'm not sure."]))
            tag = self.intents[predicted_index]
            responses = self.intents_responses.get(tag, [])
            if responses:
                return random.choice(responses)
            return "I'm sorry, I don't have an answer for that yet."
