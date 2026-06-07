# Fix scipy/sklearn hang on Windows by limiting thread pools
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import csv
import random
import json
from flask import Flask, request, jsonify, send_from_directory, make_response
import pandas as pd
import joblib
from dotenv import load_dotenv

import time

# Load Environment Variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

if not GEMINI_API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY not found in .env")

app = Flask(__name__, static_folder='landing_page')

# =============================================
# LAZY-LOADED GLOBALS (loaded on first use)
# =============================================
_models_loaded = False
logistic_model = None
rf_model = None
scaler = None
feature_names = None
xray_predictor = None
model_gemini = None

_db_connected = False
MOCK_DB = True
users_collection = None
predictions_collection = None
appointments_collection = None
auth_handler = None

def _ensure_db():
    """Lazy-load MongoDB connection on first use."""
    global _db_connected, MOCK_DB, users_collection, predictions_collection, appointments_collection, auth_handler
    if _db_connected:
        return
    _db_connected = True

    # Import auth (does NOT import pymongo anymore)
    from auth import UserAuth

    try:
        import certifi
        from pymongo import MongoClient
        print("Connecting to MongoDB...", flush=True)

        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tls=True,
                                 tlsAllowInvalidCertificates=True, tlsCAFile=certifi.where())
            client.admin.command('ismaster')
            print("DATABASE SYNC: Connected via SRV.", flush=True)
        except Exception as e:
            print(f"⚠️ SRV Connection failed: {e}", flush=True)
            try:
                if MONGO_URI:
                    direct_uri = MONGO_URI.replace("mongodb+srv://", "mongodb://").split("@")[0] + \
                                 "@ac-srx5lfq-shard-00-00.1fj4mhs.mongodb.net:27017," + \
                                 "ac-srx5lfq-shard-00-01.1fj4mhs.mongodb.net:27017," + \
                                 "ac-srx5lfq-shard-00-02.1fj4mhs.mongodb.net:27017/osteoai?ssl=true&replicaSet=atlas-1fj4mhs-shard-0&authSource=admin"
                    client = MongoClient(direct_uri, serverSelectionTimeoutMS=5000, tls=True,
                                         tlsAllowInvalidCertificates=True, tlsCAFile=certifi.where())
                    client.admin.command('ismaster')
                    print("DATABASE SYNC: Connected via Direct Shards!", flush=True)
                else:
                    raise Exception("MONGO_URI not found")
            except Exception as e2:
                print(f"❌ DATABASE SYNC ERROR: {e2}", flush=True)
                raise e2

        db = client.osteoai
        users_collection = db.users
        predictions_collection = db.predictions
        appointments_collection = db.appointments
        auth_handler = UserAuth(users_collection)
        MOCK_DB = False
        print("MongoDB connected successfully!", flush=True)
    except Exception as e:
        print(f"⚠️ WARNING: Could not connect to MongoDB Atlas. Switching to MOCK DB.", flush=True)
        print(f"Details: {e}", flush=True)
        users_collection = None
        predictions_collection = None
        appointments_collection = None
        auth_handler = UserAuth(None)
        MOCK_DB = True


# --- System Feature Control Enforcement ---

SYSTEM_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'system_config.json')

def check_feature_access(feature_key):
    """Helper to check if a specific feature is enabled in system_config.json."""
    if os.path.exists(SYSTEM_CONFIG_PATH):
        try:
            with open(SYSTEM_CONFIG_PATH, 'r') as f:
                config = json.load(f)
            return config.get(feature_key, True)
        except:
            return True # Fallback to enabled if file error
    return True # Default to enabled

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Endpoint for the frontend to check which features are currently enabled."""
    if os.path.exists(SYSTEM_CONFIG_PATH):
        try:
            with open(SYSTEM_CONFIG_PATH, 'r') as f:
                return jsonify(json.load(f))
        except:
            pass
    return jsonify({"clinical_analysis": True, "xray_analysis": True, "appointments": True})


def _ensure_models():
    """Lazy-load ML models on first prediction request."""
    global _models_loaded, logistic_model, rf_model, scaler, feature_names
    if _models_loaded:
        return
    _models_loaded = True
    
    try:
        models_dir = os.path.join(os.path.dirname(__file__), 'models')
        print("Loading clinical ensemble models...", flush=True)
        
        logistic_model = joblib.load(os.path.join(models_dir, 'logistic_model.pkl'))
        rf_model = joblib.load(os.path.join(models_dir, 'random_forest_model.pkl'))
        scaler = joblib.load(os.path.join(models_dir, 'scaler.pkl'))
        feature_names = joblib.load(os.path.join(models_dir, 'feature_names.pkl'))
        
        print("Clinical ensemble models loaded successfully!", flush=True)
    except Exception as e:
        print(f"❌ ERROR: Failed to load clinical models: {e}", flush=True)
        _models_loaded = False # Try again later


# =============================================
# ROUTES
# =============================================

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'login.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/register', methods=['POST'])
def register():
    _ensure_db()
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')

    if not username or not email or not password:
        return jsonify({"status": "error", "message": "Username, email, and password are required"}), 400

    try:
        result = auth_handler.register(username, email, password, phone)
        if result["status"] == "success":
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception as e:
        print(f"Registration Route Error: {e}")
        return jsonify({"status": "error", "message": "Database connection error. Please try again later."}), 503

@app.route('/login', methods=['POST'])
def login():
    _ensure_db()
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"status": "error", "message": "Email/Username and password are required"}), 400

    try:
        result = auth_handler.login(email, password)
        if result["status"] == "success":
            return jsonify(result)
        else:
            return jsonify(result), 401
    except Exception as e:
        print(f"Login Route Error: {e}")
        return jsonify({"status": "error", "message": "Login failed. Please try again."}), 500

# --- Doctor Side Data Integration ---

@app.after_request
def add_cors_headers(response):
    """Enable cross-origin access for the standalone doctor dashboard."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/api/doctor/appointments', methods=['GET'])
def get_doctor_appointments():
    _ensure_db()
    try:
        if appointments_collection is not None:
            appointments = list(appointments_collection.find({}, {"_id": 0}))
            return jsonify({"status": "success", "data": appointments})
        else:
            # Return mock data for demo if DB is down
            return jsonify({
                "status": "success", 
                "data": [
                    {"patient_name": "Mock Patient", "patient_email": "mock@example.com", "specialist_type": "Orthopedist", "appointment_date": "2026-05-10", "status": "pending"}
                ]
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/doctor/reports', methods=['GET'])
def get_doctor_reports():
    try:
        csv_path = os.path.join(os.path.dirname(__file__), 'data', 'data.csv')
        reports = []
        if os.path.exists(csv_path):
            with open(csv_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                # Take the last 50 reports for performance
                all_rows = list(reader)
                reports = all_rows[-50:] if len(all_rows) > 50 else all_rows
        
        return jsonify({"status": "success", "data": reports})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def get_medicine_analysis(name):
    """Uses Gemini to identify medicine class and predict impact/error."""
    if not name or name.strip() == "":
        return {"category": "None", "error_margin": 0, "insight": "No specific medicine provided."}

    global model_gemini
    if model_gemini is None:
        try:
            print("Lazy loading google.generativeai...", flush=True)
            import google.generativeai as genai
            if GEMINI_API_KEY:
                genai.configure(api_key=GEMINI_API_KEY)
                model_gemini = genai.GenerativeModel('gemini-pro')
                print("Gemini model initialized successfully.", flush=True)
            else:
                return {"category": "None", "error_margin": 0, "insight": "API key not found."}
        except Exception as e:
            print(f"Failed to load google.generativeai: {e}", flush=True)
            return {"category": "None", "error_margin": 50, "insight": "Could not load AI model."}

    prompt = f"""
    Analyze the medicine: '{name}'. 
    1. Categorize it into one of these classes: ['Corticosteroids', 'None']. If it's a steroid or known to heavily impact bone density, use 'Corticosteroids'. Otherwise 'None'.
    2. Estimate a 'Prediction Error/Uncertainty' percentage (0-100%) that this specific medicine introduces to an Osteoporosis risk model if classified generically.
    3. Provide a brief (1 sentence) clinical insight about how it affects bone health.
    
    Return ONLY a JSON object:
    {{"category": "CategoryName", "error_margin": 25, "insight": "Brief insight..."}}
    """
    try:
        response = model_gemini.generate_content(prompt)
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"Gemini Error: {e}")
        return {"category": "None", "error_margin": 50, "insight": "Could not identify medicine automatically."}

@app.route('/predict', methods=['POST'])
def predict():
    """Predicts osteoporosis risk based on clinical data."""
    if not check_feature_access('clinical_analysis'):
        return jsonify({"status": "error", "message": "Clinical Analysis is temporarily paused for system maintenance. Please check back shortly."}), 503
        
    _ensure_models()
    if not _models_loaded:
        return jsonify({"status": "error", "message": "Clinical models not available."}), 503
        
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    try:
        # Map frontend values to model-compatible raw data
        # Fields: Age, Gender, Hormonal Changes, Family History, Body Weight, 
        # Calcium Intake, Vitamin D Intake, Physical Activity, Smoking, Prior Fractures
        
        raw = {
            "Age": int(data.get("age", 25)),
            "Gender": data.get("gender", "Female"),
            "Hormonal Changes": data.get("hormonalChanges", "Normal"),
            "Family History": data.get("familyHistory", "No"),
            "Race": data.get("race", "Asian"),
            "Body Weight": data.get("bodyWeight", "Normal"),
            "Calcium Intake": data.get("calciumIntake", "Adequate"),
            "Vitamin D Intake": data.get("vitaminDIntake", "Sufficient"),
            "Physical Activity": data.get("physicalActivity", "Active"),
            "Smoking": data.get("smoking", "No"),
            "Alcohol Consumption": data.get("alcoholConsumption", "None"),
            "Prior Fractures": data.get("priorFractures", "No")
        }

        input_df = pd.DataFrame([raw])
        
        # Encoding (match the logic from training)
        input_encoded = pd.get_dummies(input_df)
        input_encoded = input_encoded.reindex(columns=feature_names, fill_value=0)

        # Scaling
        input_scaled = scaler.transform(input_encoded)

        # Ensemble Prediction (Logistic Regression + Random Forest mean)
        # Using simple mean for the demo ensemble
        lr_proba = logistic_model.predict_proba(input_scaled)[0][1]
        rf_proba = rf_model.predict_proba(input_scaled)[0][1]
        
        avg_proba = (lr_proba + rf_proba) / 2
        prediction = 1 if avg_proba > 0.5 else 0
        
        # Get cluster (if needed)
        # kmeans_model = joblib.load('models/kmeans_model.pkl') # Lazy load if needed
        # cluster = kmeans_model.predict(input_scaled)[0]

        result = {
            "status": "success",
            "risk_score": round(avg_proba * 100, 1),
            "prediction": "High Risk" if prediction == 1 else "Low Risk",
            "details": {
                "logistic_regression": round(lr_proba * 100, 1),
                "random_forest": round(rf_proba * 100, 1),
                "prediction_class": int(prediction)
            }
        }
        
        # --- Save to MongoDB (History) ---
        user_email = data.get("user_email")
        if predictions_collection is not None and user_email:
            try:
                from datetime import datetime
                predictions_collection.insert_one({
                    "user_email": user_email,
                    "type": "Clinical Analysis",
                    "prediction": result["prediction"],
                    "score": result["risk_score"],
                    "timestamp": datetime.now().isoformat()
                })
                print(f"Clinical history saved for {user_email}", flush=True)
            except Exception as mongo_err:
                print(f"MongoDB History Error: {mongo_err}")
        
        # --- Save to Dataset (data.csv) ---
        try:
            csv_path = os.path.join(os.path.dirname(__file__), 'data', 'data.csv')
            # Generate a consistent 7-digit ID similar to existing dataset
            random_id = random.randint(1000000, 9999999)
            
            # Map values to CSV structure
            new_row = {
                "Id": random_id,
                "Age": raw["Age"],
                "Gender": raw["Gender"],
                "Hormonal Changes": raw["Hormonal Changes"],
                "Family History": raw["Family History"],
                "Race": data.get("race", "Unknown"),
                "Body Weight": raw["Body Weight"],
                "Calcium Intake": raw["Calcium Intake"],
                "Vitamin D Intake": raw["Vitamin D Intake"],
                "Physical Activity": raw["Physical Activity"],
                "Smoking": raw["Smoking"],
                "Alcohol Consumption": data.get("alcoholConsumption", "None"),
                "Medical Conditions": data.get("medicalConditions", "None"),
                "Medications": data.get("medicine", "None"),
                "Prior Fractures": raw["Prior Fractures"],
                "Osteoporosis": int(prediction)
            }
            
            # Write to CSV
            file_exists = os.path.isfile(csv_path)
            with open(csv_path, mode='a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=list(new_row.keys()))
                if not file_exists:
                    writer.writeheader()
                writer.writerow(new_row)
            
            print(f"Data persisted to CSV: {random_id}", flush=True)
            result["data_saved"] = True
            result["record_id"] = random_id
            
        except Exception as csv_err:
            print(f"CSV Persistence Error: {csv_err}")
            result["data_saved"] = False

        medicine = data.get("medicine")
        if medicine:
            med_analysis = get_medicine_analysis(medicine)
            result["medicine_impact"] = med_analysis

        return jsonify(result)

    except Exception as e:
        print(f"Prediction Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/analyze-xray', methods=['POST'])
def analyze_xray():
    if not check_feature_access('xray_analysis'):
        return jsonify({"status": "error", "message": "X-ray Texture Analysis is temporarily paused for system maintenance."}), 503
    
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No file selected"}), 400

    try:
        uploads_dir = os.path.join(os.path.dirname(__file__), 'temp_uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, file.filename)
        file.save(file_path)

        global xray_predictor
        if xray_predictor is None:
            print("Lazy loading XRayPredictor (and PyTorch)...", flush=True)
            from image_analysis.predict import XRayPredictor
            xray_predictor = XRayPredictor()

        # Call custom model prediction
        result = xray_predictor.predict(file_path)

        # Cleanup
        os.remove(file_path)

        # --- Save to MongoDB (History) ---
        user_email = request.form.get('user_email')
        if result["status"] == "success" and predictions_collection is not None and user_email:
            try:
                from datetime import datetime
                predictions_collection.insert_one({
                    "user_email": user_email,
                    "type": "X-ray Analysis",
                    "prediction": result["prediction"],
                    "score": round(result["confidence"] * 100, 1),
                    "timestamp": datetime.now().isoformat()
                })
                print(f"X-ray history saved for {user_email}", flush=True)
            except Exception as mongo_err:
                print(f"MongoDB History Error: {mongo_err}")

        if result["status"] == "success":
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/user/history', methods=['POST', 'OPTIONS'])
def get_user_history():
    if request.method == 'OPTIONS':
        return '', 200
    
    _ensure_db()
    data = request.json
    user_email = data.get("user_email")
    if not user_email:
        return jsonify({"status": "error", "message": "Email is required"}), 400
        
    try:
        if predictions_collection is not None:
            records = list(predictions_collection.find(
                {"user_email": user_email}, 
                {"_id": 0}
            ).sort("timestamp", -1).limit(20))
            return jsonify({"status": "success", "data": records})
        else:
            return jsonify({"status": "error", "message": "Database offline"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    if not check_feature_access('appointments'):
        return jsonify({"status": "error", "message": "Appointment Booking is temporarily unavailable."}), 503
    
    _ensure_db()
    data = request.json

    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    try:
        appointment = {
            "patient_name": data.get("patient_name"),
            "patient_email": data.get("patient_email"),
            "patient_phone": data.get("patient_phone"),
            "specialist_type": data.get("specialist_type"),
            "appointment_date": data.get("appointment_date"),
            "appointment_time": data.get("appointment_time"),
            "additional_notes": data.get("additional_notes", ""),
            "status": "pending"
        }

        if appointments_collection is not None:
            appointments_collection.insert_one(appointment)
            print(f"✅ Appointment saved for {appointment['patient_name']} to MongoDB.")
        else:
            print(f"⚠️ MOCK DB: Appointment for {appointment['patient_name']} received but not saved.")

        return jsonify({"status": "success", "message": "Appointment booked successfully"}), 201
    except Exception as e:
        print(f"Booking Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("Serving from folder:", os.path.abspath(app.static_folder))
    #add ssl_context
    app.run(debug=True, port=8000, ssl_context='adhoc', host='0.0.0.0')
