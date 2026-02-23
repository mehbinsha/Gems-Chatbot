# backend/services/chat_service.py
from backend.config import Config

# Two possible engines: rule-based and ML wrapper
from backend.nlp.rule_based import ChatbotAssistant as RuleAssistant
from backend.services.intent_service import IntentService

class ChatService:
    def __init__(self):
        self.intent_service = IntentService()
        intents_path = Config.INTENTS_PATH
        if Config.USE_ML:
            # Try ML engine; fallback to rule-based if ML fails
            try:
                from backend.nlp.ml_engine import ChatbotML
                self.engine = ChatbotML(model_path=Config.ML_MODEL_PATH,
                                       dims_path=Config.ML_DIMENSIONS_PATH,
                                       intents_path=intents_path)
                print("Using ML engine.")
            except Exception as e:
                print("Failed to initialize ML engine:", e)
                print("Falling back to rule-based engine.")
                self.engine = RuleAssistant(intents_path)
        else:
            self.engine = RuleAssistant(intents_path)

    def get_response(self, message: str) -> str:
        # Admin updates are stored in DB and should take effect immediately.
        try:
            db_intents = self.intent_service.get_intents()
            if db_intents:
                return self.intent_service.get_response(message)
        except Exception:
            # If DB is unavailable, fallback to the previous file/ML behavior.
            pass
        return self.engine.get_response(message)
