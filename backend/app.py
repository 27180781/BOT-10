# backend/app.py

import os
import google.generativeai as genai
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect, Column, Integer, String, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import certifi
import traceback

# טען משתני סביבה מקובץ .env
load_dotenv()

print("--- Flask app starting ---")

# --- הגדרות מסד הנתונים ---
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

if not DATABASE_URL:
    print("שגיאה קריטית: משתנה הסביבה DATABASE_URL אינו מוגדר.")
else:
    try:
        print(f"--- Attempting create_engine with URL: '{DATABASE_URL}' ---")
        engine = create_engine(DATABASE_URL)
        print(f"--- Database engine object CREATED: {engine} ---")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("--- SessionLocal created ---")

        def init_db():
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

                    # ---- Seeding ----
                    print(f"--- Seeding initial data into '{FAQ.__tablename__}' table ---")
                    seed_session: Session = SessionLocal()
                    try:
                        sample_faqs = [
                            {'question': 'מהן שעות הפעילות שלכם?', 'answer': 'אנחנו פתוחים בימים א-ה בין השעות 09:00 בבוקר ל-17:00 אחר הצהריים.'},
                            {'question': 'מה הכתובת של העסק?', 'answer': 'הכתובת שלנו היא רחוב הדוגמא 12, תל אביב.'},
                            {'question': 'איך אפשר ליצור קשר?', 'answer': 'ניתן ליצור קשר בטלפון 03-1234567 או במייל contact@example.com.'},
                            {'question': 'האם אתם פתוחים ביום שישי?', 'answer': 'לא, אנחנו סגורים בסופי שבוע (שישי ושבת).'}
                        ]
                        new_faqs = [FAQ(question=item['question'], answer=item['answer']) for item in sample_faqs]
                        seed_session.add_all(new_faqs)
                        seed_session.commit()
                        print(f"--- Successfully seeded {len(new_faqs)} FAQs ---")
                    except Exception as e_seed_commit:
                        print(f"Error during data seeding commit: {e_seed_commit}")
                        seed_session.rollback()
                    finally:
                        seed_session.close()
                    # ---- End Seeding ----
                else:
                    # בדוק אם הטבלה ריקה למרות שהיא קיימת
                    check_session: Session = SessionLocal()
                    faq_count = check_session.query(FAQ).count()
                    check_session.close()
                    print(f"--- Table '{FAQ.__tablename__}' already exists with {faq_count} rows. ---")
                    if faq_count == 0:
                         print("--- Table exists but is empty. Attempting to seed again. ---")
                         # אפשר להוסיף כאן שוב את לוגיקת ה-seeding אם רוצים לנסות למלא טבלה קיימת וריקה
                         # כרגע נשאיר את זה כך, ה-Seeding ירוץ רק אם הטבלה לא קיימת כלל

            except Exception as e_init:
                print(f"Error during DB initialization (init_db function): {e_init}")
                print(traceback.format_exc())

        if engine:
             init_db()

    except Exception as e_engine:
        print(f"שגיאה **בזמן** יצירת engine או SessionLocal: {e_engine}")
        print(traceback.format_exc())
        engine = None

print(f"--- After DB setup block, final engine state is: {engine} ---")
# --- סוף הגדרות מסד הנתונים ---


# --- הגדרות Gemini API (ללא שינוי) ---
# (קוד הגדרת Gemini נשאר כפי שהיה)
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
    # (קוד db_test נשאר כפי שהיה)
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

# --- נתיב API לטיפול בצ'אט - *** מעודכן עם RAG בסיסי *** ---
@app.route('/api/chat', methods=['POST'])
def handle_chat():
    # קבלת הודעת המשתמש - ללא שינוי
    try:
        data = request.json
        if not data or 'message' not in data: return jsonify({"error": "Missing 'message' in request body"}), 400
        user_message = data['message']
        print(f"Received message: {user_message}")
    except Exception as e:
        print(f"Error parsing request JSON: {e}")
        return jsonify({"error": "Invalid request body"}), 400

    # בדיקת תקינות API KEY - ללא שינוי
    if not google_api_key: return jsonify({"error": "Google API Key not configured"}), 500

    # ---- שלב 1: שליפת הקשר (Context) ממסד הנתונים ----
    context = "אין מידע נוסף מהמאגר." # ברירת מחדל
    retrieved_faqs = []
    if engine and SessionLocal: # ודא שהחיבור ל-DB תקין
        db: Session = SessionLocal()
        try:
            print(f"--- Retrieving FAQs from DB for RAG ---")
            # שליפה פשוטה של *כל* ה-FAQs כרגע
            retrieved_faqs = db.query(FAQ).all()
            print(f"--- Retrieved {len(retrieved_faqs)} FAQs ---")
        except Exception as e_query:
            print(f"Error retrieving FAQs from DB: {e_query}")
            # לא נעצור את הבקשה אם ה-DB נכשל, פשוט נמשיך בלי הקשר
        finally:
            db.close()

    # ---- שלב 2: בניית ה-Prompt המורחב ----
    if retrieved_faqs: # אם הצלחנו לשלוף משהו
        context_list = []
        for faq in retrieved_faqs:
            context_list.append(f"שאלה נפוצה: {faq.question}\nתשובה: {faq.answer}")
        context = "\n\n".join(context_list)

    # הרכבת ההנחיה המלאה ל-Gemini
    # (אפשר לשחק עם הנוסח של ההנחיה הזו כדי לקבל תוצאות טובות יותר)
    prompt_template = f"""
    בהתבסס על המידע הבא מהשאלות הנפוצות של העסק, ענה על שאלת המשתמש.
    אם המידע לא עוזר לענות על השאלה, ענה כמיטב יכולתך על בסיס הידע הכללי שלך.

    מידע מהשאלות הנפוצות:
    ---
    {context}
    ---

    שאלת המשתמש:
    {user_message}
    """
    final_prompt = prompt_template
    print(f"--- Final prompt for Gemini:\n{final_prompt}") # הדפסה לדיבוג

    # ---- שלב 3: קריאה ל-Gemini עם ה-Prompt המורחב ----
    try:
        model = genai.GenerativeModel('gemini-2.0-flash') # או gemini-1.5-flash-latest
        print("--- Sending AUGMENTED request to Gemini API ---")
        response = model.generate_content(final_prompt) # שולחים את הפרומפט שבנינו
        print("--- Received response from Gemini API ---")
        llm_reply = response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return jsonify({"error": f"Failed to get response from LLM: {str(e)}"}), 500

    # החזרת התשובה למשתמש - ללא שינוי
    return jsonify({'reply': llm_reply})

# --- בלוק הרצת שרת הפיתוח ---
if __name__ == '__main__':
    app.run(debug=True, port=5001)