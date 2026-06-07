from api import app
from waitress import serve
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting OsteoAI Production Server on http://localhost:{port}")
    print("✨ Serving with Waitress (Production Grade WSGI)")
    serve(app, host='0.0.0.0', port=port, threads=6)
