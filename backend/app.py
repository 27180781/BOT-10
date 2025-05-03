# backend/app.py (Minimal Version for Testing)
from flask import Flask
from flask_cors import CORS
import os

print("--- Minimal Flask App Starting ---")
app = Flask(__name__)
CORS(app) # עדיין נאפשר CORS
print("--- Minimal Flask App Created ---")

@app.route('/')
def minimal_home():
    print("--- Reached Minimal / route ---")
    return "Minimal App Says Hello!"

@app.route('/ping')
def minimal_ping():
    print("--- Reached Minimal /ping route ---")
    return "Minimal Pong!"

print("--- Minimal Routes Defined ---")

# Main execution block for Flask dev server (Render uses this)
if __name__ == '__main__':
     port = int(os.environ.get("PORT", 5001))
     host = '0.0.0.0'
     print(f"--- Minimal App Starting Development Server on {host}:{port} ---")
     # נריץ בלי debug הפעם לבדיקה נקייה
     app.run(debug=False, port=port, host=host)