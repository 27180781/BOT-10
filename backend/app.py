# backend/app.py - גרסה נקייה לשלב 4

import os
import google.generativeai as genai
from flask import Flask, jsonify, request
from dotenv import load_dotenv

load_dotenv()

print("--- Flask app starting ---") # שיניתי קצת את ההדפסה

try:
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("שגיאה: משתנה הסביבה GOOGLE_API_KEY אינו מוגדר.")
    else:
        genai.configure(api_key=google_api_key)
        print("--- Google Generative AI SDK configured ---")
except Exception as e:
    print(f"שגיאה בהגדרת Google Generative AI SDK: {e}")
    google_api_key = None

app = Flask(__name__)

@app.route('/')
def home(): return "Hello from Chatbot Backend!"
@app.route('/health')
def health_check(): return jsonify({"status": "OK", "message": "Backend is running"}), 200
@app.route('/api/chat', methods=['POST'])
def handle_chat():
    try:
        data = request.json
        if not data or 'message' not in data: return jsonify({"error": "Missing 'message' in request body"}), 400
        user_message = data['message']
        print(f"Received message: {user_message}")
        if not google_api_key: return jsonify({"error": "Google API Key not configured"}), 500
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            print("--- Sending request to Gemini API ---")
            response = model.generate_content(user_message)
            print("--- Received response from Gemini API ---")
            llm_reply = response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return jsonify({"error": f"Failed to get response from LLM: {str(e)}"}), 500
        return jsonify({'reply': llm_reply})
    except Exception as e:
        print(f"Error handling chat request: {e}")
        return jsonify({"error": "An internal error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001) # שים לב: debug=True טוב לפיתוח, נצטרך לכבות אותו לפני עלייה לייצור (production)
