from werkzeug.security import generate_password_hash, check_password_hash

class UserAuth:

    
    def __init__(self, collection):
        self.collection = collection

    def register(self, username, email, password, phone):
        """Registers a new user if the email doesn't exist."""
        import re
        # Domain part must start with a letter to prevent things like kamla@123gmail.com
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z][a-zA-Z0-9-]*\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, email):
            return {"status": "error", "message": "Invalid email format. The domain part cannot start with a number."}

        if not phone or not re.match(r"^\d{10}$", phone):
            return {"status": "error", "message": "Phone number must be exactly 10 digits."}

        if self.collection is None:
            return {"status": "success", "message": "Registration successful (Mock Mode - No DB)."}

        if self.collection.find_one({"email": email}):
            return {"status": "error", "message": "User with this email already exists."}
        
        if self.collection.find_one({"phone": phone}):
            return {"status": "error", "message": "Phone number already registered."}

        # We also check if username is taken for safety
        if username and self.collection.find_one({"username": username}):
             return {"status": "error", "message": "Username already taken."}

        hashed_password = generate_password_hash(password)
        user_data = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "phone": phone
        }
        try:
            self.collection.insert_one(user_data)
            return {"status": "success", "message": "Registration successful."}
        except Exception as e:
            return {"status": "error", "message": f"Database error: {str(e)}"}

    def login(self, email, password):
        """Authenticates a user."""
        if self.collection is None:
            # Allow login for demo purposes if DB is down
            return {
                "status": "success", 
                "message": "Login successful (Mock Mode).",
                "user": {
                    "username": email or "Guest",
                    "email": email or "guest@example.com",
                    "phone": "9999999999"
                }
            }
            
        user = self.collection.find_one({"email": email})
        if not user:
            # Maybe they entered username instead of email?
            user = self.collection.find_one({"username": email})
            if not user:
                return {"status": "error", "message": "User not found."}
        
        if not user or 'password' not in user:
            return {"status": "error", "message": "Invalid credentials or corrupt user profile."}
            
        if check_password_hash(user['password'], password):
            return {
                "status": "success", 
                "message": "Login successful.",
                "user": {
                    "username": user.get("username", email),
                    "email": user.get("email", email),
                    "phone": user.get("phone", "")
                }
            }
        else:
            return {"status": "error", "message": "Incorrect password."}
