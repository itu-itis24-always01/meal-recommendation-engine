// ===== CONFIGURATION =====
const API_BASE_URL = 'http://localhost:3000/api'; // Change this to your Python server URL

// ===== GLOBAL VARIABLES =====
let currentUser = null;
let userPreferences = { liked: [], disliked: [], neutral: [] };
let allMeals = []; // Store all meals that have been recommended

// Sample meals for demo
const sampleMeals = [
    {
        name: "Vegetarian Pasta Primavera",
        description: "Fresh seasonal vegetables including bell peppers, zucchini, and cherry tomatoes tossed with pasta in a light herb olive oil sauce.",
        price: 12.99,
        ingredients: ["Pasta", "Bell Peppers", "Zucchini", "Cherry Tomatoes", "Olive Oil", "Fresh Herbs"]
    },
    {
        name: "Grilled Chicken Caesar Salad",
        description: "Crispy romaine lettuce topped with grilled chicken breast, parmesan cheese, and homemade croutons with Caesar dressing.",
        price: 14.99,
        ingredients: ["Romaine Lettuce", "Grilled Chicken", "Parmesan Cheese", "Croutons", "Caesar Dressing"]
    },
    {
        name: "Beef Burger Deluxe",
        description: "Juicy beef patty with lettuce, tomato, cheese, pickles, and special sauce on a brioche bun, served with fries.",
        price: 16.99,
        ingredients: ["Beef Patty", "Brioche Bun", "Lettuce", "Tomato", "Cheese", "Pickles", "Special Sauce"]
    },
    {
        name: "Salmon Teriyaki Bowl",
        description: "Grilled salmon glazed with teriyaki sauce served over steamed rice with mixed vegetables.",
        price: 18.99,
        ingredients: ["Salmon", "Teriyaki Sauce", "Steamed Rice", "Mixed Vegetables", "Sesame Seeds"]
    }
];

// ===== ANIMATION FUNCTIONS =====
function createFeedbackAnimation(type) {
    const animation = document.createElement('div');
    animation.className = `feedback-animation ${type}`;
    
    const icons = {
        like: '💚',
        dislike: '💔',
        neutral: '🤔'
    };
    
    animation.textContent = icons[type];
    document.body.appendChild(animation);
    
    setTimeout(() => {
        animation.remove();
    }, 1200);
}

function createParticleEffect(type, count = 8) {
    const particles = document.querySelector('.particles');
    
    for (let i = 0; i < count; i++) {
        const particle = document.createElement('div');
        particle.className = `particle ${type}`;
        
        // Random size between 4-12px
        const size = Math.random() * 8 + 4;
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        
        // Random starting position around center of screen
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;
        particle.style.left = (centerX + (Math.random() - 0.5) * 200) + 'px';
        particle.style.top = (centerY + (Math.random() - 0.5) * 200) + 'px';
        
        particles.appendChild(particle);
        
        setTimeout(() => {
            particle.remove();
        }, 1500);
    }
}

function showBudgetError(message) {
    const budgetCircle = document.getElementById('budgetCircle');
    
    // Remove existing error message
    const existingError = budgetCircle.querySelector('.budget-error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Add error class for animation
    budgetCircle.classList.add('error');
    
    // Create error message
    const errorMsg = document.createElement('div');
    errorMsg.className = 'budget-error-message';
    errorMsg.textContent = message;
    budgetCircle.appendChild(errorMsg);
    
    // Remove error class after animation
    setTimeout(() => {
        budgetCircle.classList.remove('error');
    }, 600);
    
    // Remove error message after animation
    setTimeout(() => {
        if (errorMsg.parentNode) {
            errorMsg.remove();
        }
    }, 3000);
}

// ===== SCREEN MANAGEMENT =====
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    document.getElementById(screenId).classList.add('active');

    // Load settings data when opening settings
    if (screenId === 'settings' && currentUser) {
        loadSettingsData();
    }
}

// ===== REGISTRATION SYSTEM =====
document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('registerSuccess', 'Registration successful! Please sign in.');
            setTimeout(() => showScreen('login'), 2000);
        } else {
            showError('registerError', data.error || 'Registration failed!');
        }
    } catch (error) {
        console.error('Registration error:', error);
        // Demo mode - simulate successful registration
        showSuccess('registerSuccess', 'Demo: Registration successful! Please sign in.');
        setTimeout(() => showScreen('login'), 2000);
    }
});

// ===== LOGIN SYSTEM =====
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentUser = data.user;
            currentUser.password = password; // Store password for settings display
            document.getElementById('userName').textContent = currentUser.name;
            await loadUserPreferences(); // Load preferences after login
            showScreen('mainApp');
        } else {
            showError('loginError', data.error || 'Invalid credentials!');
        }
    } catch (error) {
        console.error('Login error:', error);
        // Demo mode - simulate successful login
        currentUser = { id: 1, name: 'Demo User', email: email, password: password };
        document.getElementById('userName').textContent = currentUser.name;
        await loadUserPreferences();
        showScreen('mainApp');
    }
});

// ===== MEAL RECOMMENDATION SYSTEM =====
async function getMealRecommendation() {
    const budget = document.getElementById('budgetInput').value;
    
    if (!budget || budget <= 0) {
        showBudgetError('Please enter a valid budget!');
        return;
    }
    
    if (budget > 1000) {
        showBudgetError('Budget too high! Max $1000');
        return;
    }
    
    if (budget < 5) {
        showBudgetError('Budget too low! Min $5');
        return;
    }
    
    showScreen('loading');
    
    try {
        const response = await fetch(`${API_BASE_URL}/get-recommendation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                userId: currentUser.id,
                budget: parseFloat(budget)
            })
        });
        
        const recommendation = await response.json();
        
        if (recommendation.success) {
            displayRecommendation(recommendation.data);
        } else {
            showBudgetError('Failed to get recommendation');
            showScreen('mainApp');
        }
    } catch (error) {
        console.error('Recommendation error:', error);
        // Demo mode - show random meal within budget
        setTimeout(() => {
            const budgetNum = parseFloat(budget);
            const affordableMeals = sampleMeals.filter(meal => meal.price <= budgetNum);
            
            if (affordableMeals.length > 0) {
                const randomMeal = affordableMeals[Math.floor(Math.random() * affordableMeals.length)];
                displayRecommendation(randomMeal);
            } else {
                const cheapMeal = {
                    name: "Budget Special",
                    description: "A delicious and affordable meal perfect for your budget!",
                    price: Math.min(budgetNum - 1, 8.99),
                    ingredients: ["Fresh ingredients", "Special seasonings", "Chef's touch"]
                };
                displayRecommendation(cheapMeal);
            }
        }, 1500);
    }
}

// ===== DISPLAY RECOMMENDATION =====
function displayRecommendation(recommendation) {
    const card = document.getElementById('recommendationCard');
    
    // Add to neutral meals if not already rated
    if (!allMeals.find(meal => meal.name === recommendation.name)) {
        allMeals.push(recommendation);
        if (!userPreferences.liked.find(meal => meal.name === recommendation.name) &&
            !userPreferences.disliked.find(meal => meal.name === recommendation.name)) {
            userPreferences.neutral.push(recommendation);
        }
    }
    
    card.innerHTML = `
        <div class="meal-title">${recommendation.name}</div>
        <div class="meal-description">${recommendation.description}</div>
        <div class="meal-price">Price: ${recommendation.price}</div>
        <div class="rating-buttons">
            <button class="rating-btn thumbs-up" onclick="rateMeal('${recommendation.name}', 'like')">
                👍 Like
            </button>
            <button class="rating-btn rate-later" onclick="rateMeal('${recommendation.name}', 'neutral')">
                🤔 Later
            </button>
            <button class="rating-btn thumbs-down" onclick="rateMeal('${recommendation.name}', 'dislike')">
                👎 Ehh
            </button>
        </div>
    `;
    showScreen('recommendation');
}

// ===== RATING SYSTEM =====
async function rateMeal(mealName, rating) {
    // Add click animation to button
    const buttons = document.querySelectorAll('.rating-btn');
    buttons.forEach(btn => {
        if (btn.onclick && btn.onclick.toString().includes(rating)) {
            btn.classList.add('clicked');
            setTimeout(() => btn.classList.remove('clicked'), 600);
        }
    });
    
    // Create visual feedback
    createFeedbackAnimation(rating);
    createParticleEffect(rating);
    
    try {
        const response = await fetch(`${API_BASE_URL}/rate-meal`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                userId: currentUser.id,
                mealName: mealName,
                rating: rating
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update local preferences immediately
            const meal = allMeals.find(m => m.name === mealName);
            if (meal) {
                // Remove from all categories
                userPreferences.liked = userPreferences.liked.filter(m => m.name !== mealName);
                userPreferences.disliked = userPreferences.disliked.filter(m => m.name !== mealName);
                userPreferences.neutral = userPreferences.neutral.filter(m => m.name !== mealName);
                
                // Add to appropriate category
                if (rating === 'like') {
                    userPreferences.liked.push(meal);
                } else if (rating === 'dislike') {
                    userPreferences.disliked.push(meal);
                } else {
                    userPreferences.neutral.push(meal);
                }
            }
        }
    } catch (error) {
        console.error('Rating error:', error);
        // Demo mode - update preferences locally
        const meal = allMeals.find(m => m.name === mealName);
        if (meal) {
            // Remove from all categories
            userPreferences.liked = userPreferences.liked.filter(m => m.name !== mealName);
            userPreferences.disliked = userPreferences.disliked.filter(m => m.name !== mealName);
            userPreferences.neutral = userPreferences.neutral.filter(m => m.name !== mealName);
            
            // Add to appropriate category
            if (rating === 'like') {
                userPreferences.liked.push(meal);
            } else if (rating === 'dislike') {
                userPreferences.disliked.push(meal);
            } else {
                userPreferences.neutral.push(meal);
            }
        }
    }
}

// ===== SETTINGS FUNCTIONALITY =====
async function loadUserPreferences() {
    try {
        // Initialize preferences structure
        userPreferences = { liked: [], disliked: [], neutral: [] };
    } catch (error) {
        console.error('Error loading preferences:', error);
        userPreferences = { liked: [], disliked: [], neutral: [] };
    }
}

function loadSettingsData() {
    // Load user account information
    document.getElementById('settingsName').value = currentUser.name;
    document.getElementById('settingsEmail').value = currentUser.email;
    document.getElementById('settingsPassword').value = '••••••••';
    
    // Load preferences
    displayPreferences();
}

function displayPreferences() {
    const likedList = document.getElementById('likedMealsList');
    const dislikedList = document.getElementById('dislikedMealsList');
    const neutralList = document.getElementById('neutralMealsList');
    
    // Display liked meals
    if (userPreferences.liked.length === 0) {
        likedList.innerHTML = '<div class="empty-preferences">No liked meals yet. Start rating meals to see them here!</div>';
    } else {
        likedList.innerHTML = userPreferences.liked.map(meal => `
            <div class="preference-item liked" onclick="showMealDetails('${meal.name}')">
                <div class="meal-info">
                    <span class="meal-name">${meal.name}</span>
                    <span class="meal-price-display">${meal.price}</span>
                </div>
                <div class="preference-actions" onclick="event.stopPropagation()">
                    <button class="action-btn neutral" onclick="moveMeal('${meal.name}', 'neutral')">Later</button>
                    <button class="action-btn dislike" onclick="moveMeal('${meal.name}', 'dislike')">👎</button>
                    <button class="action-btn remove" onclick="removeMeal('${meal.name}')">Remove</button>
                </div>
            </div>
        `).join('');
    }
    
    // Display neutral/unrated meals
    if (userPreferences.neutral.length === 0) {
        neutralList.innerHTML = '<div class="empty-preferences">No unrated meals yet.</div>';
    } else {
        neutralList.innerHTML = userPreferences.neutral.map(meal => `
            <div class="preference-item neutral" onclick="showMealDetails('${meal.name}')">
                <div class="meal-info">
                    <span class="meal-name">${meal.name}</span>
                    <span class="meal-price-display">${meal.price}</span>
                </div>
                <div class="preference-actions" onclick="event.stopPropagation()">
                    <button class="action-btn like" onclick="moveMeal('${meal.name}', 'liked')">👍</button>
                    <button class="action-btn dislike" onclick="moveMeal('${meal.name}', 'dislike')">👎</button>
                    <button class="action-btn remove" onclick="removeMeal('${meal.name}')">Remove</button>
                </div>
            </div>
        `).join('');
    }
    
    // Display disliked meals
    if (userPreferences.disliked.length === 0) {
        dislikedList.innerHTML = '<div class="empty-preferences">No disliked meals yet.</div>';
    } else {
        dislikedList.innerHTML = userPreferences.disliked.map(meal => `
            <div class="preference-item disliked" onclick="showMealDetails('${meal.name}')">
                <div class="meal-info">
                    <span class="meal-name">${meal.name}</span>
                    <span class="meal-price-display">${meal.price}</span>
                </div>
                <div class="preference-actions" onclick="event.stopPropagation()">
                    <button class="action-btn like" onclick="moveMeal('${meal.name}', 'liked')">👍</button>
                    <button class="action-btn neutral" onclick="moveMeal('${meal.name}', 'neutral')">Later</button>
                    <button class="action-btn remove" onclick="removeMeal('${meal.name}')">Remove</button>
                </div>
            </div>
        `).join('');
    }
}

// ===== MEAL DETAILS MODAL =====
function showMealDetails(mealName) {
    const meal = allMeals.find(m => m.name === mealName);
    if (!meal) return;
    
    const modal = document.getElementById('mealDetailModal');
    const content = document.getElementById('mealDetailContent');
    
    const ingredients = meal.ingredients || ['Fresh ingredients', 'Quality seasonings', 'Chef\'s special touch'];
    
    content.innerHTML = `
        <div class="meal-detail-header">
            <div class="meal-detail-title">${meal.name}</div>
            <div class="meal-detail-price">${meal.price}</div>
        </div>
        <div class="meal-detail-description">${meal.description}</div>
        <div class="ingredients-section">
            <div class="ingredients-title">
                🥄 Ingredients
            </div>
            <div class="ingredients-list">
                ${ingredients.map(ingredient => `<div class="ingredient-item">${ingredient}</div>`).join('')}
            </div>
        </div>
        <div class="modal-rating-buttons">
            <button class="rating-btn thumbs-up" onclick="moveMeal('${meal.name}', 'liked'); closeMealModal();">
                👍 Like
            </button>
            <button class="rating-btn rate-later" onclick="moveMeal('${meal.name}', 'neutral'); closeMealModal();">
                🤔 Later
            </button>
            <button class="rating-btn thumbs-down" onclick="moveMeal('${meal.name}', 'disliked'); closeMealModal();">
                👎 Ehh
            </button>
        </div>
    `;
    
    modal.style.display = 'flex';
}

function closeMealModal() {
    document.getElementById('mealDetailModal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('mealDetailModal');
    if (event.target === modal) {
        closeMealModal();
    }
}

// ===== MEAL MANAGEMENT FUNCTIONS =====
async function moveMeal(mealName, newCategory) {
    const meal = allMeals.find(m => m.name === mealName);
    if (!meal) return;
    
    // Remove from all categories
    userPreferences.liked = userPreferences.liked.filter(m => m.name !== mealName);
    userPreferences.disliked = userPreferences.disliked.filter(m => m.name !== mealName);
    userPreferences.neutral = userPreferences.neutral.filter(m => m.name !== mealName);
    
    // Add to new category
    userPreferences[newCategory].push(meal);
    
    // Update display
    displayPreferences();
    
    // Call API to update server
    const ratingMap = {
        'liked': 'like',
        'disliked': 'dislike', 
        'neutral': 'neutral'
    };
    
    try {
        await rateMeal(mealName, ratingMap[newCategory]);
    } catch (error) {
        console.error('Error updating meal rating:', error);
    }
}

async function removeMeal(mealName) {
    // Remove from all preference categories
    userPreferences.liked = userPreferences.liked.filter(m => m.name !== mealName);
    userPreferences.disliked = userPreferences.disliked.filter(m => m.name !== mealName);
    userPreferences.neutral = userPreferences.neutral.filter(m => m.name !== mealName);
    
    // Remove from all meals
    allMeals = allMeals.filter(m => m.name !== mealName);
    
    displayPreferences();
    
    // Show feedback animation
    createFeedbackAnimation('neutral');
}

function togglePasswordVisibility() {
    const passwordField = document.getElementById('settingsPassword');
    const toggleBtn = document.querySelector('.toggle-password');
    
    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        passwordField.value = currentUser.password;
        toggleBtn.textContent = '🙈';
    } else {
        passwordField.type = 'password';
        passwordField.value = '••••••••';
        toggleBtn.textContent = '👁️';
    }
}

async function clearAllPreferences() {
    userPreferences = { liked: [], disliked: [], neutral: [] };
    allMeals = [];
    displayPreferences();
    
    // Show feedback animation
    createFeedbackAnimation('neutral');
}

// ===== UTILITY FUNCTIONS =====
function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    setTimeout(() => {
        errorElement.style.display = 'none';
    }, 5000);
}

function showSuccess(elementId, message) {
    const successElement = document.getElementById(elementId);
    successElement.textContent = message;
    successElement.style.display = 'block';
    setTimeout(() => {
        successElement.style.display = 'none';
    }, 3000);
}

function logout() {
    currentUser = null;
    userPreferences = { liked: [], disliked: [], neutral: [] };
    allMeals = [];
    
    // Clear form fields
    document.getElementById('budgetInput').value = '';
    document.getElementById('loginEmail').value = '';
    document.getElementById('loginPassword').value = '';
    
    showScreen('welcome');
}

// ===== INITIALIZATION =====
window.onload = function() {
    console.log('MealMate frontend loaded successfully!');
    console.log('Demo mode - API calls will use sample data');
    
    // Create particles container if it doesn't exist
    if (!document.querySelector('.particles')) {
        const particlesDiv = document.createElement('div');
        particlesDiv.className = 'particles';
        document.body.appendChild(particlesDiv);
    }
    
    // Initialize any startup functionality
    showScreen('welcome');
};