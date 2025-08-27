import openai
import json
import random
from typing import Dict, List, Optional, Tuple
from collections import Counter
import math
from dotenv import load_dotenv
import os

# ===== CHATGPT API CONFIGURATION =====
# TODO: Add your OpenAI API key here

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Replace with your actual API key
openai.api_key = OPENAI_API_KEY

def calculate_meal_compatibility_score(meal: Dict, preferences: Dict) -> float:
    """
    Calculate how compatible a meal is with user preferences using advanced scoring
    
    Args:
        meal (Dict): Meal from meals.json
        preferences (Dict): User's preference history
    
    Returns:
        float: Compatibility score (higher = better match)
    """
    score = 0.0
    
    # Extract preference data
    liked_meals = extract_meal_names(preferences.get('liked', []))
    disliked_meals = extract_meal_names(preferences.get('disliked', []))
    neutral_meals = extract_meal_names(preferences.get('neutral', []))
    
    meal_name = meal.get('name', '')
    meal_cuisine = meal.get('cuisine_type', '').lower()
    meal_category = meal.get('category', '').lower()
    meal_ingredients = [ing.lower() for ing in meal.get('ingredients', [])]
    
    # 1. DIRECT PREFERENCE MATCHING (Highest Impact)
    if meal_name in liked_meals:
        return 1000.0  # Maximum score for previously liked meals
    
    if meal_name in disliked_meals:
        return -1000.0  # Minimum score for previously disliked meals
    
    if meal_name in neutral_meals:
        score += 10.0  # Small boost for neutral meals
    
    # 2. CUISINE TYPE ANALYSIS
    liked_cuisines = get_cuisines_from_meals(preferences.get('liked', []))
    disliked_cuisines = get_cuisines_from_meals(preferences.get('disliked', []))
    
    if meal_cuisine in liked_cuisines:
        cuisine_frequency = liked_cuisines.count(meal_cuisine)
        score += 50.0 * cuisine_frequency  # More points for frequently liked cuisines
    
    if meal_cuisine in disliked_cuisines:
        cuisine_frequency = disliked_cuisines.count(meal_cuisine)
        score -= 30.0 * cuisine_frequency  # Penalty for disliked cuisines
    
    # 3. CATEGORY ANALYSIS
    liked_categories = get_categories_from_meals(preferences.get('liked', []))
    disliked_categories = get_categories_from_meals(preferences.get('disliked', []))
    
    if meal_category in liked_categories:
        category_frequency = liked_categories.count(meal_category)
        score += 30.0 * category_frequency
    
    if meal_category in disliked_categories:
        category_frequency = disliked_categories.count(meal_category)
        score -= 20.0 * category_frequency
    
    # 4. INGREDIENT COMPATIBILITY ANALYSIS
    liked_ingredients = get_ingredients_from_meals(preferences.get('liked', []))
    disliked_ingredients = get_ingredients_from_meals(preferences.get('disliked', []))
    
    # Count matching ingredients
    liked_ingredient_matches = sum(1 for ing in meal_ingredients if ing in liked_ingredients)
    disliked_ingredient_matches = sum(1 for ing in meal_ingredients if ing in disliked_ingredients)
    
    score += liked_ingredient_matches * 15.0  # Boost for liked ingredients
    score -= disliked_ingredient_matches * 10.0  # Penalty for disliked ingredients
    
    # 5. DIETARY PATTERN RECOGNITION
    if has_healthy_preference(preferences):
        healthy_keywords = ['quinoa', 'avocado', 'salmon', 'vegetables', 'salad']
        healthy_matches = sum(1 for keyword in healthy_keywords 
                            if any(keyword in ing.lower() for ing in meal_ingredients + [meal_name.lower()]))
        score += healthy_matches * 20.0
    
    if has_comfort_food_preference(preferences):
        comfort_keywords = ['cheese', 'pasta', 'pizza', 'burger', 'fries']
        comfort_matches = sum(1 for keyword in comfort_keywords 
                            if any(keyword in ing.lower() for ing in meal_ingredients + [meal_name.lower()]))
        score += comfort_matches * 15.0
    
    # 6. PRICE PREFERENCE ANALYSIS
    preferred_price_range = get_preferred_price_range(preferences)
    meal_price = meal.get('price', 0)
    
    if preferred_price_range:
        min_price, max_price = preferred_price_range
        if min_price <= meal_price <= max_price:
            score += 25.0  # Bonus for being in preferred price range
        else:
            # Small penalty for being outside preferred range
            distance_from_range = min(abs(meal_price - min_price), abs(meal_price - max_price))
            score -= distance_from_range * 2.0
    
    # 7. DIVERSITY BONUS (Encourage trying new things)
    if not preferences.get('liked') and not preferences.get('disliked'):
        # New user - recommend popular items
        popular_cuisines = ['italian', 'american', 'mexican']
        if meal_cuisine in popular_cuisines:
            score += 40.0
    else:
        # Existing user - small bonus for new cuisines/categories
        if meal_cuisine not in (liked_cuisines + disliked_cuisines):
            score += 10.0  # Encourage culinary exploration
    
    return score

def extract_meal_names(meal_list: List) -> List[str]:
    """Extract meal names from mixed format preference list"""
    names = []
    for item in meal_list:
        if isinstance(item, dict):
            names.append(item.get('name', ''))
        else:
            names.append(str(item))
    return [name for name in names if name]

def get_cuisines_from_meals(meal_list: List) -> List[str]:
    """Extract cuisine types from user's meal history"""
    cuisines = []
    # Note: This would ideally look up cuisines from the full meal database
    # For now, we'll use some heuristics based on meal names
    meal_names = extract_meal_names(meal_list)
    
    cuisine_keywords = {
        'italian': ['pizza', 'pasta', 'margherita', 'primavera'],
        'mexican': ['burrito', 'tacos', 'salsa', 'guacamole'],
        'asian': ['stir fry', 'pad thai', 'sushi', 'rice'],
        'american': ['burger', 'sandwich', 'caesar', 'bbq'],
        'mediterranean': ['gyro', 'bowl', 'quinoa', 'feta'],
        'indian': ['curry', 'tikka', 'masala'],
        'thai': ['pad thai', 'curry'],
        'greek': ['gyro', 'tzatziki', 'olives']
    }
    
    for meal_name in meal_names:
        meal_lower = meal_name.lower()
        for cuisine, keywords in cuisine_keywords.items():
            if any(keyword in meal_lower for keyword in keywords):
                cuisines.append(cuisine)
                break
    
    return cuisines

def get_categories_from_meals(meal_list: List) -> List[str]:
    """Extract categories from user's meal history"""
    categories = []
    meal_names = extract_meal_names(meal_list)
    
    category_keywords = {
        'salad': ['salad', 'bowl', 'quinoa'],
        'pizza': ['pizza', 'margherita'],
        'pasta': ['pasta', 'primavera'],
        'sandwich': ['sandwich', 'burger', 'gyro'],
        'bowl': ['bowl', 'burrito'],
        'seafood': ['salmon', 'fish', 'sushi'],
        'curry': ['curry', 'tikka', 'masala']
    }
    
    for meal_name in meal_names:
        meal_lower = meal_name.lower()
        for category, keywords in category_keywords.items():
            if any(keyword in meal_lower for keyword in keywords):
                categories.append(category)
                break
    
    return categories

def get_ingredients_from_meals(meal_list: List) -> List[str]:
    """Extract common ingredients from meal names (heuristic approach)"""
    ingredients = []
    meal_names = extract_meal_names(meal_list)
    
    common_ingredients = [
        'chicken', 'beef', 'salmon', 'fish', 'cheese', 'avocado',
        'tomato', 'lettuce', 'pasta', 'rice', 'quinoa', 'vegetables',
        'beans', 'peppers', 'onion', 'garlic', 'herbs', 'spices'
    ]
    
    for meal_name in meal_names:
        meal_lower = meal_name.lower()
        for ingredient in common_ingredients:
            if ingredient in meal_lower:
                ingredients.append(ingredient)
    
    return ingredients

def has_healthy_preference(preferences: Dict) -> bool:
    """Determine if user prefers healthy options"""
    liked_meals = extract_meal_names(preferences.get('liked', []))
    healthy_keywords = ['salad', 'quinoa', 'bowl', 'vegetarian', 'salmon', 'vegetables']
    
    healthy_count = sum(1 for meal in liked_meals 
                       if any(keyword in meal.lower() for keyword in healthy_keywords))
    
    return healthy_count >= len(liked_meals) * 0.3  # 30% or more healthy meals

def has_comfort_food_preference(preferences: Dict) -> bool:
    """Determine if user prefers comfort food"""
    liked_meals = extract_meal_names(preferences.get('liked', []))
    comfort_keywords = ['pizza', 'burger', 'pasta', 'sandwich', 'bbq', 'cheese']
    
    comfort_count = sum(1 for meal in liked_meals 
                       if any(keyword in meal.lower() for keyword in comfort_keywords))
    
    return comfort_count >= len(liked_meals) * 0.3  # 30% or more comfort food

def get_preferred_price_range(preferences: Dict) -> Optional[Tuple[float, float]]:
    """Determine user's preferred price range based on history"""
    liked_meals = preferences.get('liked', [])
    if not liked_meals:
        return None
    
    # This is a simplified approach - in a real system, you'd look up actual prices
    # For now, we'll estimate based on meal types
    estimated_prices = []
    for meal in liked_meals:
        meal_name = meal.get('name', '') if isinstance(meal, dict) else str(meal)
        meal_lower = meal_name.lower()
        
        # Estimate price based on meal type
        if any(keyword in meal_lower for keyword in ['salmon', 'steak', 'premium']):
            estimated_prices.append(18.0)
        elif any(keyword in meal_lower for keyword in ['pizza', 'pasta', 'sandwich']):
            estimated_prices.append(12.0)
        elif any(keyword in meal_lower for keyword in ['salad', 'bowl', 'soup']):
            estimated_prices.append(10.0)
        else:
            estimated_prices.append(13.0)
    
    if estimated_prices:
        avg_price = sum(estimated_prices) / len(estimated_prices)
        return (avg_price * 0.7, avg_price * 1.3)  # ±30% range
    
    return None

def get_meal_recommendation_from_chatgpt(budget: float, preferences: Dict, available_meals: List) -> Optional[Dict]:
    """
    Get intelligent meal recommendation using advanced preference analysis + ChatGPT
    
    Args:
        budget (float): User's budget for the meal
        preferences (Dict): User's liked and disliked meals {"liked": [], "disliked": [], "neutral": []}
        available_meals (List): List of available meals from meals.json
    
    Returns:
        Dict: Highly personalized meal recommendation
    """
    
    try:
        # 1. FILTER MEALS BY BUDGET
        affordable_meals = [meal for meal in available_meals if meal.get('price', 0) <= budget]
        
        if not affordable_meals:
            return get_fallback_recommendation(budget, preferences)
        
        # 2. CALCULATE COMPATIBILITY SCORES FOR ALL MEALS
        scored_meals = []
        for meal in affordable_meals:
            score = calculate_meal_compatibility_score(meal, preferences)
            scored_meals.append((meal, score))
        
        # 3. SORT BY SCORE (HIGHEST FIRST)
        scored_meals.sort(key=lambda x: x[1], reverse=True)
        
        # 4. SELECT TOP CANDIDATES (Top 3-5 meals for ChatGPT to choose from)
        top_candidates = [meal for meal, score in scored_meals[:5] if score > -100]
        
        if not top_candidates:
            # If all meals have very low scores, take the best available
            top_candidates = [scored_meals[0][0]] if scored_meals else affordable_meals[:3]
        
        # 5. CREATE ADVANCED PROMPT FOR CHATGPT
        meals_context = "TOP RECOMMENDED MEALS based on user's preference analysis:\n"
        
        for i, meal in enumerate(top_candidates):
            score = next((s for m, s in scored_meals if m == meal), 0)
            meals_context += f"\n{i+1}. {meal.get('name', 'Unknown')} (Compatibility Score: {score:.1f})\n"
            meals_context += f"   Price: ${meal.get('price', 0)} | Cuisine: {meal.get('cuisine_type', 'Unknown')}\n"
            meals_context += f"   Description: {meal.get('description', '')}\n"
            meals_context += f"   Ingredients: {', '.join(meal.get('ingredients', []))}\n"
            meals_context += f"   Category: {meal.get('category', 'Unknown')}\n"
        
        # 6. ANALYZE USER PREFERENCES FOR CONTEXT
        preference_analysis = analyze_user_preferences(preferences)
        
        # 7. BUILD INTELLIGENT PROMPT
        prompt = f"""
You are an AI sommelier and meal recommendation expert. Based on advanced preference analysis, I've identified the best meal matches for this user.

USER PROFILE & BUDGET:
- Budget: ${budget}
- {preference_analysis}

{meals_context}

RECOMMENDATION STRATEGY:
1. The meals above are pre-scored based on the user's preference history, ingredient compatibility, cuisine preferences, and dietary patterns
2. Higher compatibility scores indicate better matches for this specific user
3. Choose the meal that best balances the user's demonstrated preferences with the opportunity to delight them
4. Consider the user's preference patterns when making your final decision

RESPONSE FORMAT (return valid JSON only):
{{
    "id": actual_id_from_menu,
    "name": "Exact Name from Menu",
    "description": "Exact description from menu", 
    "price": actual_price_from_menu,
    "cuisine_type": "Exact cuisine type from menu",
    "ingredients": ["exact", "ingredients", "from", "menu"],
    "category": "Exact category from menu",
    "recommendation_reason": "Brief explanation of why this meal is perfect for this user based on their preferences"
}}

Select the meal that will make this user happiest based on their demonstrated preferences. Return only valid JSON.
        """
        
        # 8. CALL CHATGPT API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert meal recommendation AI that understands user preferences deeply and selects meals that will delight users. Respond only in valid JSON format."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=600,
            temperature=0.3  # Lower temperature for more consistent, preference-based recommendations
        )
        
        # 9. PARSE AND VALIDATE RESPONSE
        chatgpt_response = response.choices[0].message.content.strip()
        
        try:
            recommendation = json.loads(chatgpt_response)
            
            # Validate that the recommended meal exists in our top candidates
            recommended_meal_name = recommendation.get('name', '')
            valid_meal = None
            
            for meal in top_candidates:
                if meal.get('name', '') == recommended_meal_name:
                    valid_meal = meal.copy()
                    # Add the recommendation reason if provided
                    if 'recommendation_reason' in recommendation:
                        valid_meal['recommendation_reason'] = recommendation['recommendation_reason']
                    break
            
            if valid_meal:
                return valid_meal
            else:
                print(f"ChatGPT recommended meal not in top candidates: {recommended_meal_name}")
                # Return the highest scored meal as fallback
                return scored_meals[0][0] if scored_meals else get_fallback_recommendation(budget, preferences)
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse ChatGPT JSON response: {e}")
            print(f"Raw response: {chatgpt_response}")
            # Return the highest scored meal as fallback
            return scored_meals[0][0] if scored_meals else get_fallback_recommendation(budget, preferences)
            
    except Exception as e:
        print(f"ChatGPT API error: {e}")
        return get_fallback_recommendation(budget, preferences)

def analyze_user_preferences(preferences: Dict) -> str:
    """Generate a detailed analysis of user preferences for the ChatGPT prompt"""
    
    liked_meals = extract_meal_names(preferences.get('liked', []))
    disliked_meals = extract_meal_names(preferences.get('disliked', []))
    neutral_meals = extract_meal_names(preferences.get('neutral', []))
    
    analysis_parts = []
    
    # Preference summary
    if liked_meals:
        analysis_parts.append(f"Previously liked meals: {', '.join(liked_meals)}")
    else:
        analysis_parts.append("New user with no previous likes")
    
    if disliked_meals:
        analysis_parts.append(f"Previously disliked meals: {', '.join(disliked_meals)}")
    
    if neutral_meals:
        analysis_parts.append(f"Neutral about: {', '.join(neutral_meals)}")
    
    # Cuisine preferences
    liked_cuisines = get_cuisines_from_meals(preferences.get('liked', []))
    if liked_cuisines:
        cuisine_counts = Counter(liked_cuisines)
        top_cuisines = [f"{cuisine} ({count}x)" for cuisine, count in cuisine_counts.most_common(3)]
        analysis_parts.append(f"Preferred cuisines: {', '.join(top_cuisines)}")
    
    # Dietary patterns
    if has_healthy_preference(preferences):
        analysis_parts.append("Shows preference for healthy/nutritious options")
    
    if has_comfort_food_preference(preferences):
        analysis_parts.append("Shows preference for comfort food")
    
    # Price preferences
    price_range = get_preferred_price_range(preferences)
    if price_range:
        min_price, max_price = price_range
        analysis_parts.append(f"Typical price range: ${min_price:.2f} - ${max_price:.2f}")
    
    return " | ".join(analysis_parts) if analysis_parts else "New user - recommend popular options"

def get_fallback_recommendation(budget: float, preferences: Dict) -> Dict:
    """
    Intelligent fallback recommendation using the same scoring algorithm
    """
    
    # Import here to avoid circular imports
    import os
    
    # Load meals from meals.json
    meals_file_path = '../data/meals.json'
    try:
        if os.path.exists(meals_file_path):
            with open(meals_file_path, 'r') as file:
                available_meals = json.load(file)
        else:
            available_meals = get_predefined_fallback_meals()
    except Exception as e:
        print(f"Error loading meals.json: {e}")
        available_meals = get_predefined_fallback_meals()
    
    # Filter meals that fit the budget
    affordable_meals = [meal for meal in available_meals if meal.get('price', 0) <= budget]
    
    if not affordable_meals:
        if available_meals:
            return min(available_meals, key=lambda x: x.get('price', 0))
        else:
            return get_predefined_fallback_meals()[0]
    
    # Use the same scoring algorithm
    scored_meals = []
    for meal in affordable_meals:
        score = calculate_meal_compatibility_score(meal, preferences)
        scored_meals.append((meal, score))
    
    # Return the highest scored meal
    scored_meals.sort(key=lambda x: x[1], reverse=True)
    return scored_meals[0][0]

def get_predefined_fallback_meals():
    """Get predefined fallback meals in case meals.json is not available"""
    return [
        {
            "id": 999,
            "name": "Grilled Chicken Caesar Salad",
            "description": "Fresh romaine lettuce, grilled chicken breast, parmesan cheese, croutons, and caesar dressing. A healthy and satisfying meal perfect for your budget.",
            "price": 12.99,
            "cuisine_type": "American",
            "ingredients": ["Chicken Breast", "Romaine Lettuce", "Parmesan Cheese", "Croutons", "Caesar Dressing"],
            "category": "Salad"
        },
        {
            "id": 998,
            "name": "Vegetarian Pasta Primavera",
            "description": "Fresh seasonal vegetables including bell peppers, zucchini, and cherry tomatoes tossed with pasta in a light herb olive oil sauce.",
            "price": 10.25,
            "cuisine_type": "Italian",
            "ingredients": ["Pasta", "Bell Peppers", "Zucchini", "Cherry Tomatoes", "Olive Oil", "Herbs"],
            "category": "Pasta"
        },
        {
            "id": 997,
            "name": "Quinoa Buddha Bowl",
            "description": "Nutritious bowl with quinoa, roasted vegetables, avocado, and tahini dressing",
            "price": 9.99,
            "cuisine_type": "Healthy",
            "ingredients": ["Quinoa", "Roasted Vegetables", "Avocado", "Tahini", "Seeds"],
            "category": "Bowl"
        }
    ]

# ===== HELPER FUNCTIONS =====

def test_chatgpt_connection():
    """Test if ChatGPT API is working"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, respond with 'API working'"}],
            max_tokens=10
        )
        return True
    except Exception as e:
        print(f"ChatGPT API test failed: {e}")
        return False

def validate_api_key():
    """Validate if API key is properly configured"""
    if not OPENAI_API_KEY or OPENAI_API_KEY == os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OpenAI API key not configured!")
        print("📝 Please add your API key in chatgpt_service.py")
        print("🔗 Get your API key from: https://platform.openai.com/api-keys")
        return False
    return True

# ===== TESTING =====
if __name__ == "__main__":
    # Test the service
    print("🧪 Testing Advanced ChatGPT Recommendation Service...")
    
    if validate_api_key():
        print("✅ API key configured")
        if test_chatgpt_connection():
            print("✅ ChatGPT API connection successful")
        else:
            print("❌ ChatGPT API connection failed")
    else:
        print("❌ API key not configured")
    
    # Test advanced recommendation with sample preferences
    test_preferences = {
        "liked": ["Margherita Pizza", "Vegetarian Pad Thai"],
        "disliked": ["Spicy Food", "BBQ Pulled Pork Sandwich"],
        "neutral": ["Greek Gyro Plate"]
    }
    
    print(f"🧠 Testing preference analysis...")
    analysis = analyze_user_preferences(test_preferences)
    print(f"📊 User analysis: {analysis}")
    
    fallback = get_fallback_recommendation(15.0, test_preferences)
    print(f"🍽️ Smart fallback recommendation: {fallback['name']} - ${fallback['price']}")
    
    # Test scoring algorithm
    sample_meal = {
        "name": "Vegetarian Pasta Primavera",
        "cuisine_type": "Italian",
        "category": "Pasta",
        "ingredients": ["Pasta", "Bell Peppers", "Zucchini", "Cherry Tomatoes"],
        "price": 10.25
    }
    
    score = calculate_meal_compatibility_score(sample_meal, test_preferences)
    print(f"🎯 Compatibility score for sample meal: {score:.1f}")