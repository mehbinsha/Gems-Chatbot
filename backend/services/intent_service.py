import random
import re
from typing import Any

from backend.models import Intent


class IntentService:
    @staticmethod
    def _clean_and_tokenize(text: str) -> list[str]:
        cleaned = re.sub(r"[^\w\s]", " ", (text or "").lower())
        return [token for token in cleaned.split() if token.strip()]

    def get_intents(self) -> list[dict[str, Any]]:
        rows = Intent.query.order_by(Intent.tag.asc()).all()
        return [row.to_dict() for row in rows]

    def get_response(self, user_message: str) -> str:
        message = (user_message or "").strip()
        if not message:
            return "Please type a message."

        intents = self.get_intents()
        if not intents:
            return "No intents are configured yet."

        user_tokens = set(self._clean_and_tokenize(message))
        best_intent = None
        best_score = 0.0

        for intent in intents:
            token_set = set()
            for pattern in intent.get("patterns", []):
                token_set.update(self._clean_and_tokenize(pattern))

            if not token_set:
                continue

            overlap = len(user_tokens & token_set)
            union_size = len(user_tokens | token_set) or 1
            score = overlap / union_size
            if score > best_score:
                best_score = score
                best_intent = intent

        if best_intent and best_intent.get("responses"):
            return random.choice(best_intent["responses"])

        fallback = next((x for x in intents if x.get("tag") == "fallback"), None)
        if fallback and fallback.get("responses"):
            return random.choice(fallback["responses"])

        return "I'm sorry, I didn't catch that. Could you rephrase?"

    def preview_intent(self, intent_id: int) -> str:
        intent = Intent.query.get_or_404(intent_id)
        responses = intent.responses or []
        if not responses:
            return "No responses configured for this intent."
        return random.choice(responses)
