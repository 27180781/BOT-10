# backend/app.py (Step: Add Back Gemini Config)

import os
# <<< הוספנו את הייבוא של Gemini >>>
import google.generativeai as genai
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect, Column, Integer, String, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker, Session
# import certifi # לא חייבים לייבא אם לא משתמשים ישירות
import traceback

load_dotenv()
print("--- Flask app starting (with DB Init + Gemini Config) ---") # הודעה מעודכנת

# --- Database Setup (ללא שינוי) ---
DATABASE_URL = os.getenv("DATABASE_URL"); print(f"--- Value read for DATABASE_URL: '{DATABASE_URL}' ---"); engine = None; SessionLocal = None; Base = declarative_base(); db_setup_error = None
class FAQ(Base): __tablename__ = 'faqs'; id = Column(Integer, primary_key=True, index=True); question = Column(String, nullable=False, index=True); answer = Column(String, nullable=False)
def seed_data(db_session: Session): #... (ללא שינוי) ...
    try: print(f"--- Attempting to seed initial data into '{FAQ.__tablename__}' table ---"); sample_faqs = [{'question': 'מהן שעות הפעילות שלכם?', 'answer': 'אנחנו פתוחים בימים א-ה בין השעות 09:00 בבוקר ל-17:00 אחר הצהריים.'}, {'question': 'מה הכתובת של העסק?', 'answer': 'הכתובת שלנו היא רחוב הדוגמא 12, תל אביב.'},{'question': 'איך אפשר ליצור קשר?', 'answer': 'ניתן ליצור קשר בטלפון 03-1234567 או במייל contact@example.com.'}, {'question': 'האם אתם פתוחים ביום שישי?', 'answer': 'לא, אנחנו סגורים בסופי שבוע (שישי ושבת).'}]; new_faqs = [FAQ(question=item['question'], answer=item['answer']) for item in sample_faqs]; db_session.add_all(new_faqs); db_session.commit(); print(f"--- Successfully seeded {len(new_faqs)} FAQs ---")
    except Exception as e_seed_commit: print(f"Error during data seeding commit: {e_seed_commit}"); print(traceback.format_exc()); db_session.rollback()
def init_db(): #... (ללא שינוי) ...
    if not engine or not SessionLocal: print("--- Skipping DB init because engine or SessionLocal is None ---"); return
    db: Session = SessionLocal();
    try: print(f"--- Checking if table '{FAQ.__tablename__}' exists... ---"); inspector = inspect(engine); table_exists = inspector.has_table(FAQ.__tablename__)
        if not table_exists: print(f"--- Creating table '{FAQ.__tablename__}' ---"); Base.metadata.create_all(bind=engine); print(f"--- Table '{FAQ.__tablename__}' created successfully ---"); seed_data(db)
        else: print(f"--- Table '{FAQ.__tablename__}' already exists ---"); faq_count = db.query(FAQ).count(); print(f"--- Table '{FAQ.__tablename__}' exists with {faq_count} rows. ---");
            if faq_count == 0: print("--- Table exists but is empty. Calling seed function. ---"); seed_data(db)
    except Exception as e_init: print(f"Error during DB initialization (init_db function): {e_init}"); print(traceback.format_exc())
    finally:
         if db: db.close(); print("--- Closed init_db session ---")
if not DATABASE_URL: print("CRITICAL ERROR: DATABASE_URL environment variable not set."); db_setup_error = "DATABASE_URL not set"
else:
    try: print(f"--- Attempting create_engine with URL: '{DATABASE_URL}' ---"); engine = create_engine(DATABASE_URL); print(f"--- Database engine object CREATED: {engine} ---"); SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine); print("--- SessionLocal created ---");
        if engine: init_db() # קריאה לאתחול
    except Exception as e_engine: print(f"ERROR during engine or SessionLocal creation: {e_engine}"); print(traceback.format_exc()); engine = None; db_setup_error = str(e_engine)
print(f"--- After DB setup block, final engine state is: {engine} ---")
# --- End Database Setup ---


# --- Gemini API Setup <<< הוספנו חזרה ---
google_api_key = None
gemini_model = None
# chat_session = None # Not needed in this step
gemini_setup_error = None # For health check
try:
    print("--- Attempting to get GOOGLE_API_KEY from env ---")
    google_api_key_from_env = os.getenv("GOOGLE_API_KEY")
    if not google_api_key_from_env:
        print("ERROR: GOOGLE_API_KEY environment variable not set.")
        gemini_setup_error = "GOOGLE_API_KEY not set"
    else:
        google_api_key = google_api_key_from_env
        print("--- Attempting genai.configure() ---")
        genai.configure(api_key=google_api_key)
        print("--- genai.configure() finished ---")
        model_name = 'gemini-2.0-flash' # Model that worked for user
        print(f"--- Attempting genai.GenerativeModel('{model_name}') ---")
        gemini_model = genai.GenerativeModel(model_name) # Create the model object
        print(f"--- Google Generative AI SDK configured with model: {model_name} ---")
except Exception as e_sdk:
    print(f"ERROR configuring Google Generative AI SDK or Model: {e_sdk}")
    print(traceback.format_exc())
    gemini_setup_error = str(e_sdk)
print(f"--- Finished Gemini API Setup block. gemini_model is: {gemini_model} ---")
# --- End Gemini API Setup ---


# --- Prompt Template Setup (עדיין לא פעיל כי אין /api/chat) ---
# DEFAULT_PROMPT_TEMPLATE = """..."""
# PROMPT_TEMPLATE = os.getenv("PROMPT_TEMPLATE", DEFAULT_PROMPT_TEMPLATE).strip()
# print(f"--- Using prompt template...")
# --- End Prompt Template Setup ---


# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)
print("--- Flask app object created and CORS enabled ---")
# --- End Flask App Initialization ---


# --- Final check print ---
print("--- Flask routes definitions should be complete now ---")
# -----------------------


# --- Routes ---
@app.route('/')
def home(): # <<< חזר לשם המקורי
    print("--- Reached / route ---")
    return "App with DB Init + Gemini Config!" # <<< הודעה מעודכנת

@app.route('/health')
def health_check():
    print("--- Reached /health route ---")
    db_status = "OK" if engine and SessionLocal else f"Error ({db_setup_error or 'Unknown'})"
    # <<< בדיקה מעודכנת לסטטוס LLM >>>
    llm_status = "OK" if google_api_key and gemini_model else f"Error ({gemini_setup_error or 'Unknown'})"
    return jsonify({
        "status": "OK", "message": "Backend is running",
        "db_connection_setup": db_status,
        "llm_configured": llm_status # <<< נוסף סטטוס LLM
    }), 200

@app.route('/db-test')
def db_test():
    # (ללא שינוי)
    print(f"--- Reached /db-test route. Engine state: {engine} ---");
    if not engine or not SessionLocal: return jsonify({"status": "Error", "message": "Database connection not configured properly or engine is None."}), 500
    db: Session = SessionLocal(); faq_count = -1
    try: faq_count = db.query(FAQ).count(); return jsonify({"status": "OK", "message": f"DB Connection OK. Found {faq_count} FAQs."})
    except Exception as e: print(f"Error during DB test query: {e}"); return jsonify({"status": "Error", "message": f"DB query failed: {str(e)}"}), 500
    finally:
        if 'db' in locals() and db: db.close()

# (עדיין אין /api/chat)

# --- Main execution block ---
if __name__ == '__main__':
     port = int(os.environ.get("PORT", 5001))
     host = '0.0.0.0'
     print(f"--- App+DB+Init+Gemini Starting Development Server on {host}:{port} ---")
     app.run(debug=False, port=port, host=host) # עדיין מריצים ישירות לבדיקה