# backend/app.py

import os
import google.generativeai as genai
from flask import Flask, jsonify, request
from dotenv import load_dotenv
# --- ייבואים חדשים ---
from sqlalchemy import create_engine, text, inspect, Column, Integer, String, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import certifi # נשאיר למקרה שנצטרך בעתיד, לא מזיק
import traceback
# --------------------

# טען משתני סביבה מקובץ .env
load_dotenv()

print("--- Flask app starting ---")

# --- הגדרות מסד הנתונים עם הדפסות נוספות ---
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"--- Value read for DATABASE_URL: '{DATABASE_URL}' ---") # חשוב לראות מה הערך שנקרא

engine = None
SessionLocal = None

if not DATABASE_URL:
    print("שגיאה קריטית: משתנה הסביבה DATABASE_URL אינו מוגדר.")
else:
    try:
        print(f"--- Attempting create_engine with URL: '{DATABASE_URL}' ---")
        engine = create_engine(DATABASE_URL)
        print(f"--- Database engine object CREATED: {engine} ---")

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("--- SessionLocal created ---")

        Base = declarative_base()
        class FAQ(Base):
            __tablename__ = 'faqs'
            id = Column(Integer, primary_key=True, index=True)
            question = Column(String, nullable=False, index=True)
            answer = Column(String, nullable=False)

        def init_db():
            # חשוב לוודא ש-engine נוצר לפני שמנסים להשתמש בו
            if not engine:
                print("--- Skipping DB init because engine is None ---")
                return
            try:
                print(f"--- Checking if table '{FAQ.__tablename__}' exists... ---")
                inspector = inspect(engine)
                if not inspector.has_table(FAQ.__tablename__):
                    print(f"--- Creating table '{FAQ.__tablename__}' ---")
                    Base.metadata.create_all(bind=engine)
                    print(f"--- Table '{FAQ.__tablename__}' created successfully ---")
                else:
                    print(f"--- Table '{FAQ.__tablename__}' already exists ---")
            except Exception as e_init:
                print(f"Error during DB initialization (init_db function): {e_init}")
                print(traceback.format_exc())

        # קריאה לפונקציה בעת עליית האפליקציה רק אם engine נוצר
        if engine:
             init_db()

    except Exception as e_engine:
        print(f"שגיאה **בזמן** יצירת engine או SessionLocal: {e_engine}")
        print(traceback.format_exc())
        engine = None

print(f"--- After DB setup block, final engine state is: {engine} ---")
# --- סוף הגדרות מסד הנתונים ---


# --- הגדרות Gemini API ---
google_api_key = None
try:
    google_api_key_from_env = os.getenv("GOOGLE_API_KEY")
    if not google_api_key_from_env:
        print("שגיאה: משתנה הסביבה GOOGLE_API_KEY אינו מוגדר.")
    else:
        google_api_key = google_api_key_from_env
        genai.configure(api_key=google_api_key)
        print("--- Google Generative AI SDK configured ---")
except Exception as e:
    print(f"שגיאה בהגדרת Google Generative AI SDK: {e}")
# --- סוף הגדרות Gemini API ---


app = Flask(__name__)

# --- נתיבים ---
@app.route('/')
def home(): return "Hello from Chatbot Backend!"
@app.route('/health')
def health_check(): return jsonify({"status": "OK", "message": "Backend is running"}), 200

@app.route('/db-test')
def db_test():
    print(f"--- Reached /db-test route. Engine state: {engine} ---")
    if not engine or not SessionLocal:
        return jsonify({"status": "Error", "message": "Database connection not configured properly or engine is None."}), 500
    db: Session = SessionLocal()
    try:
        faq_count = db.query(FAQ).count()
        return jsonify({"status": "OK", "message": f"DB Connection OK. Found {faq_count} FAQs."})
    except Exception as e:
        print(f"Error during DB test query: {e}")
        return jsonify({"status": "Error", "message": f"DB query failed: {str(e)}"}), 500
    finally:
        db.close()

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    # ... (קוד כפי שהיה, ודא שהוא משתמש במודל שעבד לך כמו gemini-2.0-flash) ...
    try:
        data = request.json
        if not data or 'message' not in data: return jsonify({"error": "Missing 'message' in request body"}), 400
        user_message = data['message']
        print(f"Received message: {user_message}")
        if not google_api_key: return jsonify({"error": "Google API Key not configured"}), 500
        try:
            # --- ודא ששם המודל הוא זה שעבד לך קודם ---
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

# --- בלוק הרצת שרת הפיתוח ---
if __name__ == '__main__':
    app.run(debug=True, port=5001)
