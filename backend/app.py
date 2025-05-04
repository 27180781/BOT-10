# backend/app.py (ABSOLUTE MINIMUM FOR LOCAL SYNTAX CHECK)
from flask import Flask, jsonify # הוספנו jsonify למקרה שנצטרך
from flask_cors import CORS
import os
import traceback # למקרה שנצטרך בהמשך

print("--- Minimal App Starting ---")
app = Flask(__name__)
CORS(app)
print("--- Minimal App Created ---")

@app.route('/')
def minimal_home():
    print("--- Reached Minimal / route ---")
    return "Minimal App Works!"

@app.route('/health')
def minimal_health():
    print("--- Reached Minimal /health route ---")
    # החזרת תשובה פשוטה, בלי בדיקות DB או LLM
    return jsonify({"status": "OK", "message": "Minimal backend running"}), 200

print("--- Minimal Routes Defined ---")

# Main execution block for Flask dev server
if __name__ == '__main__':
     port = int(os.environ.get("PORT", 5001))
     host = '0.0.0.0'
     print(f"--- Minimal App Starting Development Server on {host}:{port} ---")
     # debug=False כי זה נבדק בסביבת Render כרגע
     app.run(debug=False, port=port, host=host)