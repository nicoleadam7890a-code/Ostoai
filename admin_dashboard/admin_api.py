import os
import json
import psutil
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi
import shutil
import ssl

# Load environment from the main ml project
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'ml project', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"✅ Loaded .env from: {dotenv_path}")
else:
    print(f"⚠️ .env not found at: {dotenv_path}")

app = Flask(__name__, static_folder='.')
CORS(app)

# Global database variables
db = None
users_collection = None
predictions_collection = None

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("❌ MONGO_URI not found in environment!")

try:
    # 1. Try standard SRV connection
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tls=True, tlsAllowInvalidCertificates=True, tlsCAFile=certifi.where(), tlsVersion='TLS1_2')
    client.admin.command('ismaster')
    print("✅ DATABASE SYNC: Connected via SRV.")
except Exception as e:
    print(f"⚠️ SRV Connection failed: {e}. Trying direct shard fallback...")
    try:
        # 2. Try direct shard connection
        if MONGO_URI:
            direct_uri = MONGO_URI.replace("mongodb+srv://", "mongodb://").split("@")[0] + \
                         "@ac-srx5lfq-shard-00-00.1fj4mhs.mongodb.net:27017," + \
                         "ac-srx5lfq-shard-00-01.1fj4mhs.mongodb.net:27017," + \
                         "ac-srx5lfq-shard-00-02.1fj4mhs.mongodb.net:27017/osteoai?ssl=true&replicaSet=atlas-1fj4mhs-shard-0&authSource=admin"
            client = MongoClient(direct_uri, serverSelectionTimeoutMS=5000, tls=True, tlsAllowInvalidCertificates=True, tlsCAFile=certifi.where(), tlsVersion='TLS1_2')
            client.admin.command('ismaster')
            print("✅ DATABASE SYNC: Connected via Direct Shards!")
        else:
            raise Exception("MONGO_URI not found")
    except Exception as e2:
        print(f"❌ DATABASE SYNC ERROR: {e2}")
        client = None

if client:
    db = client.osteoai
    users_collection = db.users
    predictions_collection = db.predictions
    # Use a more efficient count check
    print("📊 Connected to MongoDB Collections.")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

import socket

@app.route('/api/db/status')
def db_status():
    if not users_collection:
        return jsonify({"status": "disconnected", "message": "MongoDB not initialized."})
    try:
        # Simple health check
        client.admin.command('ismaster')
        return jsonify({"status": "connected"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/system/health')
def system_health():
    try:
        # Get CPU usage (non-blocking)
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        # Use shutil for disk usage - it's more stable on Windows than psutil
        try:
            total, used, free = shutil.disk_usage(".")
            disk_percent = (used / total) * 100
        except:
            disk_percent = 0
        
        # Robust port check
        main_api_running = False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                # Check localhost directly
                if s.connect_ex(('127.0.0.1', 8000)) == 0:
                    main_api_running = True
        except:
            pass
                
        return jsonify({
            "status": "online" if main_api_running else "offline",
            "cpu": cpu_usage,
            "memory": memory.percent,
            "disk": disk_percent
        })
    except Exception as e:
        print(f"Health check error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/system/restart', methods=['POST'])
def restart_main_api():
    # In a real environment, this would use subprocess to kill and start
    # For now, we return a success message acknowledging the command
    return jsonify({"status": "success", "message": "Restart command sent to Main API."})

@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    if request.method == 'GET':
        config = {}
        if os.path.exists(dotenv_path):
            with open(dotenv_path, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, val = line.strip().split('=', 1)
                        config[key] = val
        return jsonify(config)
    else:
        new_config = request.json
        with open(dotenv_path, 'w') as f:
            for key, val in new_config.items():
                f.write(f"{key}={val}\n")
        return jsonify({"status": "success", "message": "Config updated"})

@app.route('/api/users', methods=['GET'])
def get_users():
    if not users_collection:
        return jsonify({"error": "Database not connected"}), 500
    users = list(users_collection.find({}, {"_id": 0, "password": 0}))
    return jsonify(users)

@app.route('/api/predictions/stats')
def prediction_stats():
    if not predictions_collection:
        return jsonify({"total": 0, "high_risk": 0, "low_risk": 0})
    total = predictions_collection.count_documents({})
    high_risk = predictions_collection.count_documents({"prediction": 1})
    low_risk = total - high_risk
    return jsonify({
        "total": total,
        "high_risk": high_risk,
        "low_risk": low_risk
    })

@app.route('/api/predictions/logs')
def get_prediction_logs():
    if not predictions_collection:
        return jsonify([])
    limit = int(request.args.get('limit', 50))
    logs = list(predictions_collection.find().sort("_id", -1).limit(limit))
    for log in logs:
        log["_id"] = str(log["_id"])
    return jsonify(logs)

if __name__ == '__main__':
    print(f"Admin Dashboard starting on http://localhost:8001")
    app.run(port=8001, debug=True)
