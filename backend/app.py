# backend/app.py

import os
import google.generativeai as genai
from flask import Flask, jsonify, request
from flask_cors import CORS # Import CORS
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect, Column, Integer, String, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import certifi
import traceback

# Load environment variables from .env file (useful for local development)
load_dotenv()

print("--- Flask app starting ---")

# --- Database Setup ---
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"--- Value read for DATABASE_URL: '{DATABASE_URL}' ---") # Essential debug print

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
    # Make sure engine and SessionLocal were created before using them
    if not engine or not SessionLocal:
        print("--- Skipping DB init because engine or SessionLocal is None ---")
        return
    try:
        print(f"--- Checking if table '{FAQ.__tablename__}' exists... ---")
        inspector = inspect(engine)
        table_exists = inspector.has_table(FAQ.__tablename__)

        if not table_exists:
            print(f"--- Creating table '{FAQ.__tablename__}' ---")
            Base.metadata.create_all(bind=engine)
            print(f"--- Table '{FAQ.__tablename__}' created successfully ---")
            # Seed after creating table
            seed_session: Session = SessionLocal()
            try:
                seed_data(seed_session)
            finally:
                seed_session.close() # Ensure session is closed
        else:
            print(f"--- Table '{FAQ.__tablename__}' already exists ---")
            # Check if existing table is empty and seed if needed
            check_session: Session = SessionLocal()
            try:
                faq_count = check_session.query(FAQ).count()
                print(f"--- Table '{FAQ.__tablename__}' exists with {faq_count} rows. ---")
                if faq_count == 0:
                     print("--- Table exists but is empty. Calling seed function. ---")
                     # Call the seeding function within a new session context
                     seed_session: Session = SessionLocal()
                     try:
                         seed_data(seed_session)
                     finally:
                         seed_session.close()
            finally:
                 check_session.close() # Ensure check_session is closed

    except Exception as e_init:
        print(f"Error during DB initialization (init_db function): {e_init}")
        print(traceback.format_exc())

# --- Attempt to create DB engine and Session ---
if not DATABASE_URL:
    print("CRITICAL ERROR: DATABASE_URL environment variable not set.")
else:
    try:
        print(f"--- Attempting create_engine with URL: '{DATABASE_URL}' ---")
        engine = create_engine(DATABASE_URL)
        print(f"--- Database engine object CREATED: {engine} ---")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("--- SessionLocal created ---")

        # --- Initialize DB (create table/seed) ---
        # Re-enable the init_db call
        if engine:
           init_db() # <<<--- הסרנו את ה-# מכאן

    except Exception as e_engine:
        print(f"ERROR during engine or SessionLocal creation: {e_engine}")
        print(traceback.format_exc())
        engine = None # Ensure engine is None if creation failed

print(f"--- After DB setup block, final engine state is: {engine} ---")

# ... (סוף הפונקציה handle_chat) ...

print("--- Flask routes definitions should be complete now ---") 
# --- בלוק הרצת שרת הפיתוח ---
# --- End Database Setup ---


# --- Gemini API Setup ---
# (ללא שינוי)
# ...

# --- Prompt Template Setup ---
# (ללא שינוי)
# ...

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app) # Enable CORS for all routes
print("--- Flask app object created and CORS enabled ---")
# --- End Flask App Initialization ---


# --- Routes ---
# (כל הנתיבים ללא שינוי: /, /health, /db-test, /api/chat)
# ...

# --- Main execution block ---
# (ללא שינוי)
# ...