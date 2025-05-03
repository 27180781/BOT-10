# backend/app.py

import os
import google.generativeai as genai
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect, Column, Integer, String, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import certifi
import traceback

# Load environment variables from .env file
load_dotenv()
print("--- Flask app starting ---")

# --- Database Setup ---
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"--- Value read for DATABASE_URL: '{DATABASE_URL}' ---")

engine = None
SessionLocal = None
Base = declarative_base()
db_setup_error = None

# Define Data Model - FAQ
class FAQ(Base):
    __tablename__ = 'faqs'
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False, index=True)
    answer = Column(String, nullable=False)

# --- Separate function for seeding data ---
def seed_data(db_session: Session):
    try:
        print(f"--- Attempting to seed initial data into '{FAQ.__tablename__}' table ---")
        sample_faqs = [
            {'question': 'מהן שעות הפעילות שלכם?', 'answer': 'אנחנו פתוחים בימים א-ה בין השעות 09:00 בבוקר ל-17:00 אחר הצהריים.'},
            {'question': 'מה הכתובת של העסק?', 'answer': 'הכתובת שלנו היא רחוב הדוגמא 12, תל אביב.'},
            {'question': 'איך אפשר ליצור קשר?', 'answer': 'ניתן ליצור קשר בטלפון 03-1234567 או במייל contact@example.com.'},
            {'question': 'האם אתם פתוחים ביום שישי?', 'answer': 'לא, אנחנו סגורים בסופי שבוע (שישי ושבת).'}
        ]
        new_faqs = [FAQ(question=item['question'], answer=item['answer']) for item in sample_faqs]
        db_session.add_all(new_faqs)
        db_session.commit()
        print(f"--- Successfully seeded {len(new_faqs)} FAQs ---")
    except Exception as e_seed_commit:
        print(f"Error during data seeding commit: {e_seed_commit}")
        print(traceback.format_exc())
        db_session.rollback()

# --- Function to initialize DB ---
def init_db():
    if not engine or not SessionLocal:
        print("--- Skipping DB init because engine or SessionLocal is None ---")
        return
    db: Session = SessionLocal() # Create session ONCE
    try:
        print(f"--- Checking if table '{FAQ.__tablename__}' exists... ---")
        inspector = inspect(engine)
        table_exists = inspector.has_table(FAQ.__tablename__)

        if not table_exists:
            print(f"--- Creating table '{FAQ.__tablename__}' ---")
            Base.metadata.create_all(bind=engine) # Create table
            print(f"--- Table '{FAQ.__tablename__}' created successfully ---")
            seed_data(db) # Seed after creating
        else:
            print(f"--- Table '{FAQ.__tablename__}' already exists ---")
            faq_count = db.query(FAQ).count() # Check if empty
            print(f"--- Table '{FAQ.__tablename__}' exists with {faq_count} rows. ---")
            if faq_count == 0:
                 print("--- Table exists but is empty. Calling seed function. ---")
                 seed_data(db) # Seed if empty

    except Exception as e_init:
        print(f"Error during DB initialization (init_db function): {e_init}")
        print(traceback.format_exc())
    finally:
         if db: # Ensure session was created before trying to close
             db.close()
             print("--- Closed init_db session ---")
# --- End init_db ---

# --- Attempt to create DB engine and Session ---
if not DATABASE_URL:
    print("CRITICAL ERROR: DATABASE_URL environment variable not set.")
    db_setup_error = "DATABASE_URL not set"
else:
    try:
        print(f"--- Attempting create_engine with URL: '{DATABASE_URL}' ---")
        engine = create_engine(DATABASE_URL)
        print(f"--- Database engine object CREATED: {engine} ---")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("--- SessionLocal created ---")
    except Exception as e_engine:
        print(f"ERROR during engine or SessionLocal creation: {e_engine}")
        print(traceback.format_exc())
        engine = None
        db_setup_error = str(e_engine)

# --- Initialize DB (Call after trying to create engine) ---
if engine: # Check if engine was created successfully
   init_db()
# -------------------------------------------------------

print(f"--- After DB setup block, final engine state is: {engine} ---")
# --- End Database Setup ---


# --- Gemini API Setup ---
google_api_key = None
gemini_model = None
chat_session = None # Placeholder for future use
gemini_setup_error = None
try:
    google_api_key_from_env = os.getenv("GOOGLE_API_KEY")
    if not google_api_key_from_env: print("ERROR: GOOGLE_API_KEY environment variable not set."); gemini_setup_error = "GOOGLE_API_KEY not set"
    else:
        google_api_key = google_api_key_from_env; genai.configure(api_key=google_api_key)
        model_name = 'gemini-2.0-flash'; print(f"--- Attempting genai.GenerativeModel('{model_name}') ---"); gemini_model = genai.GenerativeModel(model_name); print(f"--- Google Generative AI SDK configured with model: {model_name} ---")
except Exception as e_sdk: print(f"ERROR configuring Google Generative AI SDK or Model: {e_sdk}"); print(traceback.format_exc()); gemini_setup_error = str(e_sdk)
print(f"--- Finished Gemini API Setup block. gemini_model is: {gemini_model} ---")
# --- End Gemini API Setup ---


# --- Prompt Template Setup ---
DEFAULT_PROMPT_TEMPLATE = """
ענה על שאלת המשתמש הבאה. אם המידע הנוסף המצורף מהשאלות הנפוצות רלוונטי לשאלה, השתמש בו בתשובתך. אם לא, ענה כמיטב יכולתך על בסיס הידע הכללי שלך.

{context}

שאלת המשתמש:
{user_message}
"""
PROMPT_TEMPLATE = os.getenv("PROMPT_TEMPLATE", DEFAULT_PROMPT_TEMPLATE).strip()
print(f"--- Using prompt template (loaded from env or default): ---\n{PROMPT_TEMPLATE[:200]}...")
# --- End Prompt Template Setup ---


# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app) # Enable CORS for all routes
print("--- Flask app object created and CORS enabled ---")
# --- End Flask App Initialization ---


# --- Final check print ---
print("--- Flask routes definitions should be complete now ---")
# -----------------------


# --- Routes ---
@app.route('/')
def home():
    print("--- Reached / route ---")
    return "Chatbot Backend Running!"

@app.route('/health')
def health_check():
    print("--- Reached /health route ---")
    db_status = "OK" if engine and SessionLocal else f"Error ({db_setup_error or 'Unknown'})"
    llm_status = "OK" if google_api_key and gemini_model else f"Error ({gemini_setup_error or 'Unknown'})"
    return jsonify({
        "status": "OK", "message": "Backend is running",
        "db_connection_setup": db_status,
        "llm_configured": llm_status
    }), 200

@app.route('/db-test')
def db_test():
    print(f"--- Reached /db-test route. Engine state: {engine} ---")
    if not engine or not SessionLocal: return jsonify({"status": "Error", "message": "Database connection not configured properly or engine is None."}), 500
    db: Session = SessionLocal(); faq_count = -1
    try: faq_count = db.query(FAQ).count(); return jsonify({"status": "OK", "message": f"DB Connection OK. Found {faq_count} FAQs."})
    except Exception as e: print(f"Error during DB test query: {e}"); return jsonify({"status": "Error", "message": f"DB query failed: {str(e)}"}), 500
    finally:
        if 'db' in locals() and db: db.close()

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    # Using generate_content for now as a stable baseline
    print(f"--- Reached /api/chat [POST]. ---")
    # 1. Parse User Input
    try: data = request.json; user_message = data['message'] if data and 'message' in data else None; print(f"Received message: {user_message}")
    except Exception as e: print(f"Error parsing request JSON: {e}"); return jsonify({"error": "Invalid request body"}), 400
    if not user_message: return jsonify({"error": "Missing 'message' in request body"}), 400
    # 2. Check Prerequisites
    if not google_api_key: return jsonify({"error": "Google API Key not configured"}), 500
    if not gemini_model: return jsonify({"error": "Gemini model not initialized"}), 500
    # 3. RAG - Retrieve Context
    context = "אין מידע נוסף מהמאגר."; retrieved_faqs = []
    if engine and SessionLocal:
        db: Session = SessionLocal();
        try: print(f"--- Retrieving FAQs from DB for RAG ---"); retrieved_faqs = db.query(FAQ).all(); print(f"--- Retrieved {len(retrieved_faqs)} FAQs ---")
            if retrieved_faqs: context_list = []; [context_list.append(f"Q: {faq.question}\nA: {faq.answer}") for faq in retrieved_faqs]; context = "מידע רלוונטי מהשאלות הנפוצות:\n---\n" + "\n\n".join(context_list) + "\n---"
        except Exception as e_query: print(f"Error retrieving FAQs from DB: {e_query}")
        finally:
            if 'db' in locals() and db: db.close()
    else: print("--- Skipping DB query because engine or SessionLocal is None ---")
    # 4. Format Prompt
    try: final_prompt = PROMPT_TEMPLATE.format(context=context, user_message=user_message); print(f"--- Final prompt for Gemini:\n{final_prompt[:500]}...")
    except Exception as e_format: print(f"Unexpected error formatting prompt: {e_format}"); return jsonify({"error": "Internal server error: prompt formatting failed."}), 500
    # 5. Send to Gemini
    llm_reply = "Error: LLM did not respond."
    try: print("--- Sending SINGLE request to Gemini API using generate_content ---"); response = gemini_model.generate_content(final_prompt); print("--- Received response from generate_content ---")
        if response.parts: llm_reply = response.text
        elif response.candidates and response.candidates[0].finish_reason != 'STOP': llm_reply = f"שגיאה: התגובה נחסמה. סיבה: {response.candidates[0].finish_reason}"; print(f"LLM response blocked. Reason: {response.candidates[0].finish_reason}")
        else: llm_reply = "קיבלתי תשובה ריקה מהמודל."; print(f"Warning: Received potentially empty response. Response: {response}")
    except Exception as e_send: print(f"Error calling generate_content: {e_send}"); return jsonify({"error": f"Failed to get response from LLM: {str(e_send)}"}), 500
    # 6. Return Response
    return jsonify({'reply': llm_reply})
# --- End Routes ---

# --- Main execution block ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    is_local_debug = os.getenv("RENDER") is None
    app.run(debug=is_local_debug, port=port, host='0.0.0.0')
# --- End Main execution block ---