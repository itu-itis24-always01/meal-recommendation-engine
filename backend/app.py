from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
from chatgpt_service import get_meal_recommendation_from_chatgpt

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# ===== FILE PATHS =====
USERS_FILE = '../data/users.json'
MEALS_FILE = '../data/meals.json'
PREFERENCES_FILE = '../data/preferences.json'

# ===== UTILITY FUNCTIONS =====
def load_json_file(filepath):
    """Load data from JSON file"""
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            return json.load(file)
    return []

def save_json_file(filepath, data):
    """Save data to JSON file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=2)

def find_user_by_email(email):
    """Find user by email"""
    users = load_json_file(USERS_FILE)
    return next((user for user in users if user['email'] == email), None)

def get_user_preferences(user_id):
    """Get user preferences with support for neutral category"""
    preferences = load_json_file(PREFERENCES_FILE)
    user_prefs = preferences.get(str(user_id), {"liked": [], "disliked": [], "neutral": []})
    
    # Ensure all categories exist for backward compatibility
    if "neutral" not in user_prefs:
        user_prefs["neutral"] = []
    
    return user_prefs

def save_user_preferences(user_id, preferences):
    """Save user preferences"""
    all_preferences = load_json_file(PREFERENCES_FILE)
    all_preferences[str(user_id)] = preferences
    save_json_file(PREFERENCES_FILE, all_preferences)

# ===== API ENDPOINTS =====

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        # Validation
        if not name or not email or not password:
            return jsonify({"success": False, "error": "All fields are required"}), 400
        
        # Check if user already exists
        if find_user_by_email(email):
            return jsonify({"success": False, "error": "User already exists with this email"}), 400
        
        # Load existing users
        users = load_json_file(USERS_FILE)
        
        # Create new user
        new_user = {
            "id": len(users) + 1,
            "name": name,
            "email": email,
            "password": password,  # In production, hash this password!
            "created_at": datetime.now().isoformat()
        }
        
        # Add to users list and save
        users.append(new_user)
        save_json_file(USERS_FILE, users)
        
        return jsonify({"success": True, "message": "User registered successfully"}), 201
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        # Validation
        if not email or not password:
            return jsonify({"success": False, "error": "Email and password are required"}), 400
        
        # Find user
        user = find_user_by_email(email)
        if not user or user['password'] != password:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
        
        # Return user data (exclude password)
        user_data = {
            "id": user['id'],
            "name": user['name'],
            "email": user['email']
        }
        
        return jsonify({"success": True, "user": user_data}), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/get-recommendation', methods=['POST'])
def get_recommendation():
    """Get meal recommendation using ChatGPT"""
    try:
        data = request.json
        user_id = data.get('userId')
        budget = data.get('budget')
        
        # Validation
        if not user_id or not budget:
            return jsonify({"success": False, "error": "User ID and budget are required"}), 400
        
        # Get user preferences
        preferences = get_user_preferences(user_id)
        
        # Get available meals
        available_meals = load_json_file(MEALS_FILE)
        
        # Call ChatGPT service to get recommendation
        recommendation = get_meal_recommendation_from_chatgpt(
            budget=budget,
            preferences=preferences,
            available_meals=available_meals
        )
        
        if recommendation:
            return jsonify({"success": True, "data": recommendation}), 200
        else:
            return jsonify({"success": False, "error": "Failed to get recommendation"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/rate-meal', methods=['POST'])
def rate_meal():
    """Save user meal rating with support for neutral rating"""
    try:
        data = request.json
        user_id = data.get('userId')
        meal_name = data.get('mealName')
        rating = data.get('rating')  # 'like', 'dislike', or 'neutral'
        
        # Validation
        if not user_id or not meal_name or rating not in ['like', 'dislike', 'neutral']:
            return jsonify({"success": False, "error": "Invalid data"}), 400
        
        # Get current preferences
        preferences = get_user_preferences(user_id)
        
        # Create a meal object if we only have the name
        meal_obj = {"name": meal_name, "price": 0}  # Default price, will be updated by frontend
        
        # Update preferences - remove from all categories first
        for category in ['liked', 'disliked', 'neutral']:
            preferences[category] = [meal for meal in preferences[category] 
                                   if (meal.get('name', meal) if isinstance(meal, dict) else meal) != meal_name]
        
        # Add to appropriate category based on rating
        if rating == 'like':
            preferences['liked'].append(meal_obj)
        elif rating == 'dislike':
            preferences['disliked'].append(meal_obj)
        else:  # neutral
            preferences['neutral'].append(meal_obj)
        
        # Save updated preferences
        save_user_preferences(user_id, preferences)
        
        return jsonify({"success": True, "message": "Rating saved successfully"}), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/get-user-preferences', methods=['POST'])
def get_preferences():
    """Get user preferences"""
    try:
        data = request.json
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({"success": False, "error": "User ID is required"}), 400
        
        preferences = get_user_preferences(user_id)
        return jsonify({"success": True, "preferences": preferences}), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/clear-preferences', methods=['POST'])
def clear_preferences():
    """Clear all user preferences"""
    try:
        data = request.json
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({"success": False, "error": "User ID is required"}), 400
        
        # Clear all preferences
        empty_preferences = {"liked": [], "disliked": [], "neutral": []}
        save_user_preferences(user_id, empty_preferences)
        
        return jsonify({"success": True, "message": "All preferences cleared"}), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/remove-meal', methods=['POST'])
def remove_meal():
    """Remove a specific meal from user preferences"""
    try:
        data = request.json
        user_id = data.get('userId')
        meal_name = data.get('mealName')
        
        if not user_id or not meal_name:
            return jsonify({"success": False, "error": "User ID and meal name are required"}), 400
        
        # Get current preferences
        preferences = get_user_preferences(user_id)
        
        # Remove meal from all categories
        for category in ['liked', 'disliked', 'neutral']:
            preferences[category] = [meal for meal in preferences[category] 
                                   if (meal.get('name', meal) if isinstance(meal, dict) else meal) != meal_name]
        
        # Save updated preferences
        save_user_preferences(user_id, preferences)
        
        return jsonify({"success": True, "message": "Meal removed successfully"}), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "MealMate backend is running!"}), 200

# ===== RUN SERVER =====
if __name__ == '__main__':
    print("🚀 Starting MealMate Backend Server...")
    print("📂 Data files will be stored in '../data/' directory")
    print("🌐 Frontend should connect to: http://localhost:3000/api")
    print("✨ New features: Neutral ratings, meal details, improved preferences")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=3000)