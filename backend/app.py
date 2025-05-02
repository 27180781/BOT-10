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
        # Add connection options for better pooling/timeouts if needed later
        engine = create_engine(DATABASE_URL)
        print(f"--- Database engine object CREATED: {engine} ---")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("--- SessionLocal created ---")

        # --- Initialize DB (create table/seed) ---
        # Temporarily commented out for debugging SyntaxError
        # if engine:
        #    init_db() # <<<--- THIS LINE IS COMMENTED OUT

    except Exception as e_engine:
        print(f"ERROR during engine or SessionLocal creation: {e_engine}")
        print(traceback.format_exc())
        engine = None # Ensure engine is None if creation failed

print(f"--- After DB setup block, final engine state is: {engine} ---")
# --- End Database Setup ---


# --- Gemini API Setup ---
google_api_key = None # Initialize global variable
gemini_model = None
chat_session = None # Initialize global chat session
try:
    google_api_key_from_env = os.getenv("GOOGLE_API_KEY")
    if not google_api_key_from_env:
        print("ERROR: GOOGLE_API_KEY environment variable not set.")
    else:
        google_api_key = google_api_key_from_env # Assign to global variable
        genai.configure(api_key=google_api_key)
        model_name = 'gemini-2.0-flash' # Or gemini-1.5-flash-latest
        gemini_model = genai.GenerativeModel(model_name)
        print(f"--- Google Generative AI SDK configured with model: {model_name} ---")
except Exception as e_sdk:
    print(f"ERROR configuring Google Generative AI SDK or Model: {e_sdk}")
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


# --- Routes ---
@app.route('/')
def home():
    print("--- Reached / route ---")
    return "Hello from Chatbot Backend!"

@app.route('/health')
def health_check():
    print("--- Reached /health route ---")
    # Check basic components status
    db_status = "OK" if engine and SessionLocal else "Error"
    llm_status = "OK" if google_api_key and gemini_model else "Error"
    return jsonify({
        "status": "OK",
        "message": "Backend is running",
        "db_connection": db_status,
        "llm_configured": llm_status
    }), 200

@app.route('/db-test')
def db_test():
    # This route will likely fail now or return count -1 because init_db was skipped
    print(f"--- Reached /db-test route. Engine state: {engine} ---")
    if not engine or not SessionLocal:
        return jsonify({"status": "Error", "message": "Database connection not configured properly or engine is None."}), 500

    db: Session = SessionLocal()
    faq_count = -1 # Default error value
    try:
        # This might fail if the table doesn't exist because init_db was skipped
        faq_count = db.query(FAQ).count()
        return jsonify({"status": "OK", "message": f"DB Connection OK. Found {faq_count} FAQs."})
    except Exception as e:
        print(f"Error during DB test query (maybe table missing?): {e}")
        return jsonify({"status": "Error", "message": f"DB query failed: {str(e)}"}), 500
    finally:
        # Ensure session is always closed
        if db:
            db.close()

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    global chat_session # Allow modification of the global variable
    print(f"--- Reached /api/chat [POST]. Current chat session object: {chat_session} ---")

    # 1. Parse User Input
    try:
        data = request.json
        if not data or 'message' not in data: return jsonify({"error": "Missing 'message' in request body"}), 400
        user_message = data['message']
        print(f"Received message: {user_message}")
    except Exception as e:
        print(f"Error parsing request JSON: {e}")
        return jsonify({"error": "Invalid request body"}), 400

    # 2. Check Prerequisites
    if not google_api_key: return jsonify({"error": "Google API Key not configured"}), 500
    if not gemini_model: return jsonify({"error": "Gemini model not initialized"}), 500

    # 3. Initialize Chat Session if needed
    if chat_session is None:
        try:
            print("--- Starting new chat session ---")
            chat_session = gemini_model.start_chat(history=[])
        except Exception as e_chat_start:
             print(f"Error starting chat session: {e_chat_start}")
             return jsonify({"error": "Failed to initialize chat session"}), 500

    # 4. RAG - Retrieve Context (DB Lookup)
    # This part will likely retrieve 0 FAQs because init_db was skipped
    context = "אין מידע נוסף מהמאגר." # Default context
    retrieved_faqs = []
    if engine and SessionLocal:
        db: Session = SessionLocal()
        try:
            print(f"--- Retrieving FAQs from DB for RAG ---"); retrieved_faqs = db.query(FAQ).all(); print(f"--- Retrieved {len(retrieved_faqs)} FAQs ---")
            if retrieved_faqs:
                context_list = []; [context_list.append(f"Q: {faq.question}\nA: {faq.answer}") for faq in retrieved_faqs]
                context = "מידע רלוונטי מהשאלות הנפוצות:\n---\n" + "\n\n".join(context_list) + "\n---"
        except Exception as e_query:
            # This might fail if table 'faqs' doesn't exist
            print(f"Error retrieving FAQs from DB (maybe table missing?): {e_query}")
        finally:
            if db: db.close()
    else:
        print("--- Skipping DB query because engine or SessionLocal is None ---")

    # 5. Format Prompt using Template
    try:
        final_prompt = PROMPT_TEMPLATE.format(context=context, user_message=user_message)
        print(f"--- Final prompt for Gemini:\n{final_prompt[:500]}...")
    except KeyError as e_format:
        print(f"Error formatting prompt template! Missing key: {e_format}"); print(f"Template was: {PROMPT_TEMPLATE}")
        return jsonify({"error": "Internal server error: prompt template formatting failed."}), 500
    except Exception as e_format_other:
         print(f"Unexpected error formatting prompt: {e_format_other}")
         return jsonify({"error": "Internal server error: prompt formatting failed."}), 500

    # 6. Send to Gemini via Chat Session
    llm_reply = "Error: LLM did not respond." # Default reply on error
    try:
        print("--- Sending message via chat.send_message() ---")
        response = chat_session.send_message(final_prompt)
        print("--- Received response from chat session ---")
        llm_reply = response.text
    except Exception as e_send:
        print(f"Error sending message via chat session: {e_send}")
        chat_session = None # Reset chat on error
        return jsonify({"error": f"Failed to get response from LLM chat session: {str(e_send)}"}), 500

    # 7. Return Response
    return jsonify({'reply': llm_reply})
# --- End Routes ---


# --- Main execution block ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    is_local_debug = os.getenv("RENDER") is None
    # Use host='0.0.0.0' to be accessible within Render's network
    # debug=True will be ignored by Gunicorn anyway
    app.run(debug=is_local_debug, port=port, host='0.0.0.0')
# --- End Main execution block ---