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

# Define Data Model - FAQ
class FAQ(Base):
    __tablename__ = 'faqs'
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False, index=True)
    answer = Column(String, nullable=False)

# --- Separate function for seeding data ---
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

# --- Function to initialize DB (create table + call seed) ---
def init_db():
    # (פונקציה ללא שינוי)
    if not engine or not SessionLocal: print("--- Skipping DB init because engine or SessionLocal is None ---"); return
    init_session: Session = SessionLocal()
    try:
        print(f"--- Checking if table '{FAQ.__tablename__}' exists... ---"); inspector = inspect(engine); table_exists = inspector.has_table(FAQ.__tablename__)
        if not table_exists:
            print(f"--- Creating table '{FAQ.__tablename__}' ---"); Base.metadata.create_all(bind=engine); print(f"--- Table '{FAQ.__tablename__}' created successfully ---")
            seed_data(init_session)
        else:
            print(f"--- Table '{FAQ.__tablename__}' already exists ---"); faq_count = init_session.query(FAQ).count(); print(f"--- Table '{FAQ.__tablename__}' exists with {faq_count} rows. ---")
            if faq_count == 0: print("--- Table exists but is empty. Calling seed function. ---"); seed_data(init_session)
    except Exception as e_init: print(f"Error during DB initialization (init_db function): {e_init}"); print(traceback.format_exc())
    finally: init_session.close()

# --- Attempt to create DB engine and Session ---
if not DATABASE_URL:
    print("CRITICAL ERROR: DATABASE_URL environment variable not set.")
else:
    try:
        # בלוק ה-try מכיל רק את יצירת ה-engine וה-SessionLocal
        print(f"--- Attempting create_engine with URL: '{DATABASE_URL}' ---")
        engine = create_engine(DATABASE_URL)
        print(f"--- Database engine object CREATED: {engine} ---")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("--- SessionLocal created ---")
    except Exception as e_engine:
        # בלוק ה-except תופס שגיאות מה-try שלמעלה
        print(f"ERROR during engine or SessionLocal creation: {e_engine}")
        print(traceback.format_exc())
        engine = None # Ensure engine is None if creation failed

# <<<--- כאן המיקום הנכון לקרוא ל-init_db ---<<<
# רק אחרי שניסינו (והצלחנו או נכשלנו ו-engine=None) ליצור את החיבור
if engine:
   init_db() # קוראים לפונקציה רק אם ה-engine נוצר בהצלחה
# <<<---------------------------------------<<<

print(f"--- After DB setup block, final engine state is: {engine} ---")
# --- End Database Setup ---


# --- Gemini API Setup (ללא שינוי) ---
# ... (קוד הגדרת Gemini כפי שהיה) ...

# --- Prompt Template Setup (ללא שינוי) ---
# ... (קוד קריאת הפרומפט כפי שהיה) ...

# --- Flask App Initialization (ללא שינוי) ---
app = Flask(__name__)
CORS(app)
print("--- Flask app object created and CORS enabled ---")
# --- End Flask App Initialization ---


# --- Final check print (ללא שינוי) ---
print("--- Flask routes definitions should be complete now ---")
# -----------------------


# --- Routes (ללא שינוי) ---
# ... (קוד הנתיבים /, /health, /db-test, /api/chat כפי שהיה) ...

# --- Main execution block (ללא שינוי) ---
# ... (קוד if __name__ == '__main__': כפי שהיה) ...