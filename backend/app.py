# backend/app.py

import os
import google.generativeai as genai
from flask import Flask, jsonify, request
from flask_cors import CORS # <<<--- הוספנו ייבוא
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect, Column, Integer, String, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import certifi
import traceback

# טען משתני סביבה מקובץ .env
load_dotenv()

print("--- Flask app starting ---")

# --- הגדרות מסד הנתונים ---
# (קוד הגדרת DB ללא שינוי)
DATABASE_URL = os.getenv("DATABASE_URL"); print(f"--- Value read for DATABASE_URL: '{DATABASE_URL}' ---"); engine = None; SessionLocal = None; Base = declarative_base()
class FAQ(Base): __tablename__ = 'faqs'; id = Column(Integer, primary_key=True, index=True); question = Column(String, nullable=False, index=True); answer = Column(String, nullable=False)
def seed_data(db_session: Session):
    try:
        print(f"--- Attempting to seed initial data into '{FAQ.__tablename__}' table ---"); sample_faqs = [{'question': 'מהן שעות הפעילות שלכם?', 'answer': 'אנחנו פתוחים בימים א-ה בין השעות 09:00 בבוקר ל-17:00 אחר הצהריים.'}, {'question': 'מה הכתובת של העסק?', 'answer': 'הכתובת שלנו היא רחוב הדוגמא 12, תל אביב.'},{'question': 'איך אפשר ליצור קשר?', 'answer': 'ניתן ליצור קשר בטלפון 03-1234567 או במייל contact@example.com.'}, {'question': 'האם אתם פתוחים ביום שישי?', 'answer': 'לא, אנחנו סגורים בסופי שבוע (שישי ושבת).'}]; new_faqs = [FAQ(question=item['question'], answer=item['answer']) for item in sample_faqs]; db_session.add_all(new_faqs); db_session.commit(); print(f"--- Successfully seeded {len(new_faqs)} FAQs ---")
    except Exception as e_seed_commit: print(f"Error during data seeding commit: {e_seed_commit}"); print(traceback.format_exc()); db_session.rollback()
def init_db():
    if not engine or not SessionLocal: print("--- Skipping DB init because engine or SessionLocal is None ---"); return
    try:
        print(f"--- Checking if table '{FAQ.__tablename__}' exists... ---"); inspector = inspect(engine); table_exists = inspector.has_table(FAQ.__tablename__)
        if not table_exists: print(f"--- Creating table '{FAQ.__tablename__}' ---"); Base.metadata.create_all(bind=engine); print(f"--- Table '{FAQ.__tablename__}' created successfully ---"); seed_session: Session = SessionLocal(); seed_data(seed_session); seed_session.close()
        else:
            print(f"--- Table '{FAQ.__tablename__}' already exists ---"); check_session: Session = SessionLocal(); faq_count = check_session.query(FAQ).count(); check_session.close(); print(f"--- Table '{FAQ.__tablename__}' exists with {faq_count} rows. ---")
            if faq_count == 0: print("--- Table exists but is empty. Calling seed function. ---"); seed_session: Session = SessionLocal(); seed_data(seed_session); seed_session.close()
    except Exception as e_init: print(f"Error during DB initialization (init_db function): {e_init}"); print(traceback.format_exc())
if not DATABASE_URL: print("שגיאה קריטית: משתנה הסביבה DATABASE_URL אינו מוגדר.")
else:
    try: print(f"--- Attempting create_engine with URL: '{DATABASE_URL}' ---"); engine = create_engine(DATABASE_URL); print(f"--- Database engine object CREATED: {engine} ---"); SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine); print("--- SessionLocal created ---")
        if engine: init_db()
    except Exception as e_engine: print(f"שגיאה **בזמן** יצירת engine או SessionLocal: {e_engine}"); print(traceback.format_exc()); engine = None
print(f"--- After DB setup block, final engine state is: {engine} ---")
# --- סוף הגדרות מסד הנתונים ---

# --- הגדרות Gemini API (ללא שינוי) ---
# ... (קוד הגדרת Gemini נשאר כפי שהיה) ...

# --- קריאת תבנית הפרומפט ממשתנה סביבה (ללא שינוי) ---
# ... (קוד קריאת PROMPT_TEMPLATE נשאר כפי שהיה) ...

app = Flask(__name__)
CORS(app) # <<<--- הוספנו אתחול של CORS כאן!

# --- נתיבים (ללא שינוי) ---
# ... (קוד הנתיבים /, /health, /db-test, /api/chat נשאר כפי שהיה) ...
# ... (כולל הפונקציות home, health_check, db_test, handle_chat) ...

# --- בלוק הרצת שרת הפיתוח (ללא שינוי) ---
# ... (קוד if __name__ == '__main__':) ...