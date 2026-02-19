# ml/train.py
import os
import json
import random
import argparse

import nltk
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# Ensure you have downloaded NLTK data once:
# nltk.download('punkt')
# nltk.download('wordnet')

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

class Trainer:
    def __init__(self, intents_path):
        self.intents_path = intents_path
        self.documents = []
        self.vocabulary = []
        self.intents = []
        self.intents_responses = {}

    @staticmethod
    def tokenize_and_lemmatize(text):
        from nltk.stem import WordNetLemmatizer
        from nltk.tokenize import word_tokenize
        lemmatizer = WordNetLemmatizer()
        words = word_tokenize(text)
        words = [lemmatizer.lemmatize(word.lower()) for word in words]
        return words

    def parse_intents(self):
        with open(self.intents_path, 'r', encoding='utf-8') as f:
            intents_data = json.load(f)
        for intent in intents_data['intents']:
            if intent['tag'] not in self.intents:
                self.intents.append(intent['tag'])
                self.intents_responses[intent['tag']] = intent['responses']
            for pattern in intent['patterns']:
                pattern_words = self.tokenize_and_lemmatize(pattern)
                self.vocabulary.extend(pattern_words)
                self.documents.append((pattern_words, intent['tag']))
        self.vocabulary = sorted(set(self.vocabulary))

    def bag_of_words(self, words):
        return [1 if word in words else 0 for word in self.vocabulary]

    def prepare_data(self):
        bags = []
        indices = []
        for document in self.documents:
            words = document[0]
            bag = self.bag_of_words(words)
            intent_index = self.intents.index(document[1])
            bags.append(bag)
            indices.append(intent_index)
        self.X = np.array(bags, dtype=np.float32)
        self.y = np.array(indices, dtype=np.int64)

    def train(self, epochs=100, batch_size=8, lr=0.001, model_out="./ml/model/chatbot_model.pth", dims_out="./ml/model/dimensions.json"):
        X_tensor = torch.tensor(self.X, dtype=torch.float32)
        y_tensor = torch.tensor(self.y, dtype=torch.long)
        dataset = TensorDataset(X_tensor, y_tensor)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        model = ChatbotModel(self.X.shape[1], len(self.intents))
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=lr)

        for epoch in range(epochs):
            running_loss = 0.0
            for batch_X, batch_y in loader:
                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                running_loss += loss.item()
            print(f"Epoch {epoch + 1}/{epochs} - Loss: {running_loss / len(loader):.4f}")

        os.makedirs(os.path.dirname(model_out), exist_ok=True)
        torch.save(model.state_dict(), model_out)
        with open(dims_out, 'w') as f:
            json.dump({'input_size': self.X.shape[1], 'output_size': len(self.intents)}, f)
        print("Saved model and dimensions to", model_out, dims_out)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--intents", default="../backend/nlp/intents.json")
    parser.add_argument("--epochs", type=int, default=100)
    args = parser.parse_args()

    trainer = Trainer(args.intents)
    trainer.parse_intents()
    trainer.prepare_data()
    trainer.train(epochs=args.epochs, model_out="./ml/model/chatbot_model.pth", dims_out="./ml/model/dimensions.json")
