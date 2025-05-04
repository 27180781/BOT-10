# backend/app.py (Step: Add DB Connection Objects Only)

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
# <<< ייבואים נדרשים ל-SQLAlchemy >>>
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session # הוספנו Session למקרה הצורך בהמשך
import traceback
# ----------------------------------

load_dotenv()
print("--- Flask app starting (with DB Engine Creation Only) ---") # הודעה מעודכנת

# --- Database Engine/Session Setup ---
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"--- Value read for DATABASE_URL: '{DATABASE_URL}' ---")
engine = None
SessionLocal = None
db_setup_error = None # משתנה לשמור שגיאת התקנה

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set.")
    db_setup_error = "DATABASE_URL not set"
else:
    try:
        print(f"--- Attempting create_engine with URL: '{DATABASE_URL}' ---")
        engine = create_engine(DATABASE_URL) # <<< יוצרים את המנוע
        print(f"--- Database engine object CREATED: {engine} ---")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # <<< יוצרים את יוצר הסשנים
        print("--- SessionLocal created ---")
    except Exception as e_engine:
        print(f"ERROR during engine or SessionLocal creation: {e_engine}")
        print(traceback.format_exc())
        db_setup_error = str(e_engine)
        engine = None # Ensure engine is None if creation failed
print(f"--- After DB setup block, final engine state is: {engine} ---")
# --- End Database Setup ---

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)
print("--- Flask app object created and CORS enabled ---")

# --- Final check print ---
print("--- Flask routes definitions should be complete now ---")

# --- Routes ---
@app.route('/')
def minimal_home():
    print("--- Reached / route ---")
    return "App with DB Engine Creation!" # הודעה מעודכנת

@app.route('/health')
def health_check():
    print("--- Reached /health route ---")
    # נדווח אם הצלחנו ליצור engine ו-SessionLocal
    db_status = "OK" if engine and SessionLocal else f"Error ({db_setup_error or 'Unknown'})"
    llm_status = "Not Configured Yet" # עדיין לא הוספנו LLM
    return jsonify({
        "status": "OK", "message": "Backend is running",
        "db_connection_setup": db_status,
        "llm_configured": llm_status
    }), 200

print("--- Minimal Routes + Health Check Defined ---")
# (לא מוסיפים את /db-test או /api/chat בשלב זה)

# --- Main execution block ---
if __name__ == '__main__':
     port = int(os.environ.get("PORT", 5001))
     host = '0.0.0.0'
     print(f"--- App+DB Engine Starting Development Server on {host}:{port} ---")
     app.run(debug=False, port=port, host=host)