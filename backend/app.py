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

load_dotenv()
print("--- Flask app starting ---")

# --- Database Setup ---
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"--- Value read for DATABASE_URL: '{DATABASE_URL}' ---")

engine = None
SessionLocal = None
Base = declarative_base()

class FAQ(Base):
    __tablename__ = 'faqs'
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False, index=True)
    answer = Column(String, nullable=False)

def seed_data(db_session: Session):
    # (פונקציה ללא שינוי)
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

def init_db(): # <<<--- גרסה מפושטת של הפונקציה
    if not engine or not SessionLocal:
        print("--- Skipping DB init because engine or SessionLocal is None ---")
        return

    db: Session = SessionLocal() # פותחים Session פעם אחת בהתחלה
    try:
        print(f"--- Checking if table '{FAQ.__tablename__}' exists... ---")
        inspector = inspect(engine)
        table_exists = inspector.has_table(FAQ.__tablename__)

        if not table_exists:
            print(f"--- Creating table '{FAQ.__tablename__}' ---")
            Base.metadata.create_all(bind=engine) # יוצרים טבלה
            print(f"--- Table '{FAQ.__tablename__}' created successfully ---")
            seed_data(db) # קוראים ל-seed עם ה-session הקיים
        else:
            print(f"--- Table '{FAQ.__tablename__}' already exists ---")
            faq_count = db.query(FAQ).count() # בודקים אם ריק עם ה-session הקיים
            print(f"--- Table '{FAQ.__tablename__}' exists with {faq_count} rows. ---")
            if faq_count == 0:
                 print("--- Table exists but is empty. Calling seed function. ---")
                 seed_data(db) # קוראים ל-seed עם ה-session הקיים

    except Exception as e_init:
        print(f"Error during DB initialization (init_db function): {e_init}")
        print(traceback.format_exc())
    finally:
         # סוגרים את ה-session פעם אחת בסוף, תמיד
         if 'db' in locals() and db:
             db.close()
             print("--- Closed init_db session ---")
# --- סוף init_db ---

# --- Attempt to create DB engine and Session ---
# (ללא שינוי)
if not DATABASE_URL: print("CRITICAL ERROR: DATABASE_URL environment variable not set.")
else:
    try:
        print(f"--- Attempting create_engine with URL: '{DATABASE_URL}' ---"); engine = create_engine(DATABASE_URL); print(f"--- Database engine object CREATED: {engine} ---"); SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine); print("--- SessionLocal created ---")
        # קריאה לאתחול ה-DB אחרי יצירת ה-engine
        if engine: init_db()
    except Exception as e_engine: print(f"ERROR during engine or SessionLocal creation: {e_engine}"); print(traceback.format_exc()); engine = None
print(f"--- After DB setup block, final engine state is: {engine} ---")
# --- End Database Setup ---

# --- Gemini API Setup ---
# (ללא שינוי מהגרסה הקודמת שעבדה)
google_api_key = None; gemini_model = None; chat_session = None
try:
    google_api_key_from_env = os.getenv("GOOGLE_API_KEY");
    if not google_api_key_from_env: print("ERROR: GOOGLE_API_KEY environment variable not set.")
    else: google_api_key = google_api_key_from_env; genai.configure(api_key=google_api_key); model_name = 'gemini-2.0-flash'; gemini_model = genai.GenerativeModel(model_name); print(f"--- Google Generative AI SDK configured with model: {model_name} ---")
except Exception as e_sdk: print(f"ERROR configuring Google Generative AI SDK or Model: {e_sdk}")
# --- End Gemini API Setup ---

# --- Prompt Template Setup ---
# (ללא שינוי)
DEFAULT_PROMPT_TEMPLATE = """..."""; PROMPT_TEMPLATE = os.getenv("PROMPT_TEMPLATE", DEFAULT_PROMPT_TEMPLATE).strip(); print(f"--- Using prompt template...")
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
# (כל הנתיבים ללא שינוי: /, /health, /db-test, /api/chat - עדיין עם generate_content)
# ...

# --- Main execution block ---
# (ללא שינוי)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001)); is_local_debug = os.getenv("RENDER") is None
    app.run(debug=is_local_debug, port=port, host='0.0.0.0')
# --- End Main execution block ---