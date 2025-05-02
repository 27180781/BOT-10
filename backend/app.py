# backend/app.py

import os
import google.generativeai as genai
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect, Column, Integer, String, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import certifi
import traceback

# טען משתני סביבה מקובץ .env (שימושי לפיתוח מקומי)
load_dotenv()

print("--- Flask app starting ---")

# --- הגדרות מסד הנתונים ---
# (קוד הגדרת DB ללא שינוי מהגרסה הקודמת)
# ... (DATABASE_URL, engine, SessionLocal, Base, FAQ, seed_data, init_db) ...
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"--- Value read for DATABASE_URL: '{DATABASE_URL}' ---")
engine = None
SessionLocal = None
Base = declarative_base()
class FAQ(Base):
    __tablename__ = 'faqs'; id = Column(Integer, primary_key=True, index=True); question = Column(String, nullable=False, index=True); answer = Column(String, nullable=False)
def seed_data(db_session: Session):
    try:
        print(f"--- Attempting to seed initial data into '{FAQ.__tablename__}' table ---")
        sample_faqs = [
            {'question': 'מהן שעות הפעילות שלכם?', 'answer': 'אנחנו פתוחים בימים א-ה בין השעות 09:00 בבוקר ל-17:00 אחר הצהריים.'}, {'question': 'מה הכתובת של העסק?', 'answer': 'הכתובת שלנו היא רחוב הדוגמא 12, תל אביב.'},
            {'question': 'איך אפשר ליצור קשר?', 'answer': 'ניתן ליצור קשר בטלפון 03-1234567 או במייל contact@example.com.'}, {'question': 'האם אתם פתוחים ביום שישי?', 'answer': 'לא, אנחנו סגורים בסופי שבוע (שישי ושבת).'}
        ]; new_faqs = [FAQ(question=item['question'], answer=item['answer']) for item in sample_faqs]; db_session.add_all(new_faqs); db_session.commit(); print(f"--- Successfully seeded {len(new_faqs)} FAQs ---")
    except Exception as e_seed_commit: print(f"Error during data seeding commit: {e_seed_commit}"); print(traceback.format_exc()); db_session.rollback()
def init_db():
    if not engine or not SessionLocal: print("--- Skipping DB init because engine or SessionLocal is None ---"); return
    try:
        print(f"--- Checking if table '{FAQ.__tablename__}' exists... ---"); inspector = inspect(engine); table_exists = inspector.has_table(FAQ.__tablename__)
        if not table_exists:
            print(f"--- Creating table '{FAQ.__tablename__}' ---"); Base.metadata.create_all(bind=engine); print(f"--- Table '{FAQ.__tablename__}' created successfully ---")
            seed_session: Session = SessionLocal(); seed_data(seed_session); seed_session.close()
        else:
            print(f"--- Table '{FAQ.__tablename__}' already exists ---"); check_session: Session = SessionLocal(); faq_count = check_session.query(FAQ).count(); check_session.close(); print(f"--- Table '{FAQ.__tablename__}' exists with {faq_count} rows. ---")
            if faq_count == 0: print("--- Table exists but is empty. Calling seed function. ---"); seed_session: Session = SessionLocal(); seed_data(seed_session); seed_session.close()
    except Exception as e_init: print(f"Error during DB initialization (init_db function): {e_init}"); print(traceback.format_exc())
if not DATABASE_URL: print("שגיאה קריטית: משתנה הסביבה DATABASE_URL אינו מוגדר.")
else:
    try:
        print(f"--- Attempting create_engine with URL: '{DATABASE_URL}' ---"); engine = create_engine(DATABASE_URL); print(f"--- Database engine object CREATED: {engine} ---")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine); print("--- SessionLocal created ---")
        if engine: init_db()
    except Exception as e_engine: print(f"שגיאה **בזמן** יצירת engine או SessionLocal: {e_engine}"); print(traceback.format_exc()); engine = None
print(f"--- After DB setup block, final engine state is: {engine} ---")
# --- סוף הגדרות מסד הנתונים ---


# --- הגדרות Gemini API (ללא שינוי) ---
google_api_key = None
gemini_model = None
chat_session = None
try:
    google_api_key_from_env = os.getenv("GOOGLE_API_KEY")
    if not google_api_key_from_env: print("שגיאה: משתנה הסביבה GOOGLE_API_KEY אינו מוגדר.")
    else:
        google_api_key = google_api_key_from_env; genai.configure(api_key=google_api_key)
        model_name = 'gemini-2.0-flash'; gemini_model = genai.GenerativeModel(model_name); print(f"--- Google Generative AI SDK configured with model: {model_name} ---")
except Exception as e: print(f"שגיאה בהגדרת Google Generative AI SDK או המודל: {e}")
# --- סוף הגדרות Gemini API ---


# --- קריאת תבנית הפרומפט ממשתנה סביבה ---
DEFAULT_PROMPT_TEMPLATE = """
ענה על שאלת המשתמש הבאה. אם המידע הנוסף המצורף מהשאלות הנפוצות רלוונטי לשאלה, השתמש בו בתשובתך. אם לא, ענה כמיטב יכולתך על בסיס הידע הכללי שלך.

{context}

שאלת המשתמש:
{user_message}
"""
PROMPT_TEMPLATE = os.getenv("PROMPT_TEMPLATE", DEFAULT_PROMPT_TEMPLATE).strip()
print(f"--- Using prompt template (loaded from env or default): ---\n{PROMPT_TEMPLATE[:200]}...") # הדפס את ההתחלה
# ---------------------------------------


app = Flask(__name__)

# --- נתיבים ---
@app.route('/')
def home(): return "Hello from Chatbot Backend!"
@app.route('/health')
def health_check(): return jsonify({"status": "OK", "message": "Backend is running"}), 200
@app.route('/db-test')
def db_test():
    # (קוד db_test ללא שינוי)
    print(f"--- Reached /db-test route. Engine state: {engine} ---")
    if not engine or not SessionLocal: return jsonify({"status": "Error", "message": "Database connection not configured properly or engine is None."}), 500
    db: Session = SessionLocal(); faq_count=0
    try: faq_count = db.query(FAQ).count(); return jsonify({"status": "OK", "message": f"DB Connection OK. Found {faq_count} FAQs."})
    except Exception as e: print(f"Error during DB test query: {e}"); return jsonify({"status": "Error", "message": f"DB query failed: {str(e)}"}), 500
    finally: db.close()


@app.route('/api/chat', methods=['POST'])
def handle_chat():
    global chat_session
    try:
        data = request.json
        if not data or 'message' not in data: return jsonify({"error": "Missing 'message' in request body"}), 400
        user_message = data['message']
        print(f"Received message: {user_message}")
    except Exception as e: print(f"Error parsing request JSON: {e}"); return jsonify({"error": "Invalid request body"}), 400

    if not google_api_key: return jsonify({"error": "Google API Key not configured"}), 500
    if not gemini_model: return jsonify({"error": "Gemini model not initialized"}), 500

    if chat_session is None: print("--- Starting new chat session ---"); chat_session = gemini_model.start_chat(history=[])

    # ---- שלב 1: שליפת הקשר (Context) ממסד הנתונים (ללא שינוי) ----
    context = "אין מידע נוסף מהמאגר." # ברירת מחדל אם אין DB או אין תוצאות
    retrieved_faqs = []
    if engine and SessionLocal:
        db: Session = SessionLocal()
        try:
            print(f"--- Retrieving FAQs from DB for RAG ---"); retrieved_faqs = db.query(FAQ).all(); print(f"--- Retrieved {len(retrieved_faqs)} FAQs ---")
            if retrieved_faqs:
                context_list = []; [context_list.append(f"Q: {faq.question}\nA: {faq.answer}") for faq in retrieved_faqs]
                context = "מידע רלוונטי מהשאלות הנפוצות:\n---\n" + "\n\n".join(context_list) + "\n---"
        except Exception as e_query: print(f"Error retrieving FAQs from DB: {e_query}")
        finally: db.close()

    # ---- שלב 2: שימוש בתבנית הפרומפט שנטענה מהסביבה ----
    try:
        final_prompt = PROMPT_TEMPLATE.format(context=context, user_message=user_message)
        print(f"--- Final prompt for Gemini:\n{final_prompt[:500]}...")
    except KeyError as e_format:
        print(f"Error formatting prompt template! Missing key: {e_format}")
        print(f"Template was: {PROMPT_TEMPLATE}")
        return jsonify({"error": "Internal server error: prompt template formatting failed."}), 500
    # --------------------------------------------------

    # ---- שלב 3: קריאה ל-Gemini (ללא שינוי) ----
    try:
        print("--- Sending message via chat.send_message() ---")
        response = chat_session.send_message(final_prompt)
        print("--- Received response from chat session ---")
        llm_reply = response.text
    except Exception as e:
        print(f"Error sending message via chat session: {e}"); chat_session = None
        return jsonify({"error": f"Failed to get response from LLM chat session: {str(e)}"}), 500

    return jsonify({'reply': llm_reply})

# --- בלוק הרצת שרת הפיתוח ---
if __name__ == '__main__':
    app.run(debug=True, port=5001)