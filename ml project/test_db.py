import certifi
from pymongo import MongoClient
import sys

MONGO_URI = "mongodb+srv://Ishita:Ishita%4022053018@cluster0.1fj4mhs.mongodb.net/osteoai?retryWrites=true&w=majority&appName=Cluster0"

def test_connection():
    print(f"Testing connection to: {MONGO_URI.split('@')[1]}") # Don't print password
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tls=True, tlsAllowInvalidCertificates=True, tlsCAFile=certifi.where())
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        print("✅ SUCCESS: Connected to MongoDB Atlas!")
        
        db = client.osteoai
        count = db.users.count_documents({})
        print(f"✅ SUCCESS: Accessed 'osteoai' database. User count: {count}")
        
    except Exception as e:
        print(f"❌ ERROR: Could not connect to MongoDB.")
        print(f"Details: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_connection()
