# backend/routes/chat_routes.py
from flask import Blueprint, request, jsonify
from backend.services.chat_service import ChatService

chat_bp = Blueprint("chat", __name__)
service = ChatService()

@chat_bp.route("/chat", methods=["POST"])
def chat():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    user_message = request.json.get("message", "")
    if user_message is None:
        return jsonify({"error": "No message provided"}), 400
    try:
        response_text = service.get_response(user_message)
        return jsonify({"response": response_text})
    except Exception as e:
        print("Server error:", e)
        return jsonify({"error": "An internal error occurred."}), 500
