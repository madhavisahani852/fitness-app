import os
import logging
import joblib
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Determine static folder path (one level up to find frontend/)
base_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.abspath(os.path.join(base_dir, "..", "frontend"))

app = Flask(__name__, static_folder=frontend_dir, static_url_path="")
CORS(app)  # Enable Cross-Origin Resource Sharing

# Global dictionary to hold models and encoders
models = {}

def load_models():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base_dir, "models")
    
    required_artifacts = [
        "calorie_model.pkl",
        "workout_model.pkl",
        "le_gender.pkl",
        "le_goal.pkl",
        "le_workout.pkl",
        "cv.pkl",
        "df_original.pkl",
        "lstm_scaler.pkl",
        "weight_history.pkl"
    ]
    
    logger.info("Loading pre-trained models and encoders from %s...", models_dir)
    for artifact in required_artifacts:
        path = os.path.join(models_dir, artifact)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing required artifact: {artifact} at {path}")
        key = artifact.replace(".pkl", "")
        models[key] = joblib.load(path)
    logger.info("All models loaded successfully.")

# Load models once at startup
try:
    load_models()
except Exception as e:
    logger.critical("Failed to load models during startup: %s", str(e))
    # Note: Flask app won't start if load_models fails, which is correct for prediction-only services.

@app.route("/", methods=["GET"])
def index():
    # Content negotiation: serve HTML if browser requests it, otherwise API metadata
    accept = request.headers.get("Accept", "")
    if "text/html" in accept and app.static_folder and os.path.exists(os.path.join(app.static_folder, "index.html")):
        return app.send_static_file("index.html")
    return jsonify({
        "app": "AI Fitness & Diet Recommendation API",
        "version": "1.0.0",
        "status": "running"
    }), 200

@app.route("/health", methods=["GET"])
def health():
    if not models:
        return jsonify({"status": "unhealthy", "error": "Models not loaded"}), 500
    return jsonify({"status": "healthy", "models_loaded": True}), 200

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400
        
        # 1. Validation
        required_fields = ["name", "age", "gender", "height", "weight", "sleep", "steps", "workout_hours", "goal", "diet_pref", "medical"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        name = str(data["name"]).strip()
        age = int(data["age"])
        gender = str(data["gender"]).strip()
        height = float(data["height"])
        weight = float(data["weight"])
        sleep = float(data["sleep"])
        steps = int(data["steps"])
        workout_hours = float(data["workout_hours"])
        goal = str(data["goal"]).strip()
        diet_pref = str(data["diet_pref"]).strip()
        medical = str(data["medical"]).strip()

        # Bounds validation
        if not (10 <= age <= 80):
            return jsonify({"error": "Age must be between 10 and 80"}), 400
        if not (gender in ["Male", "Female"]):
            return jsonify({"error": "Gender must be 'Male' or 'Female'"}), 400
        if not (100 <= height <= 250):
            return jsonify({"error": "Height must be between 100cm and 250cm"}), 400
        if not (30 <= weight <= 200):
            return jsonify({"error": "Weight must be between 30kg and 200kg"}), 400
        if not (1 <= sleep <= 12):
            return jsonify({"error": "Sleep must be between 1 and 12 hours"}), 400
        if not (0 <= steps <= 50000):
            return jsonify({"error": "Steps must be between 0 and 50000"}), 400
        if not (0 <= workout_hours <= 5.0):
            return jsonify({"error": "Workout hours must be between 0.0 and 5.0"}), 400
        if not (goal in ["Bulk", "Cut", "Maintain"]):
            return jsonify({"error": "Fitness goal must be 'Bulk', 'Cut', or 'Maintain'"}), 400
        if not (diet_pref in ["Balanced", "High Protein", "Low Carb", "Keto", "Vegetarian"]):
            return jsonify({"error": "Diet preference must be one of: Balanced, High Protein, Low Carb, Keto, Vegetarian"}), 400
        if not (medical in ["None", "Diabetes", "Hypertension", "Asthma"]):
            return jsonify({"error": "Medical condition must be one of: None, Diabetes, Hypertension, Asthma"}), 400

        # 2. BMI Calculation
        height_m = height / 100.0
        bmi = weight / (height_m ** 2)
        if bmi < 18.5:
            bmi_status = "Underweight"
        elif bmi < 25.0:
            bmi_status = "Normal Weight"
        elif bmi < 30.0:
            bmi_status = "Overweight"
        else:
            bmi_status = "Obese"

        # 3. BMR + Activity Factor Calories
        if gender.lower() == "male":
            bmr = 10.0 * weight + 6.25 * height - 5.0 * age + 5.0
        else:
            bmr = 10.0 * weight + 6.25 * height - 5.0 * age - 161.0
        
        activity_factor = 1.2
        if workout_hours >= 1.0:
            activity_factor = 1.55
        if workout_hours >= 2.0:
            activity_factor = 1.75
        
        bmr_calories = bmr * activity_factor
        if goal.lower() == "bulk":
            bmr_calories += 300
        elif goal.lower() == "cut":
            bmr_calories -= 300
        bmr_calories = int(round(bmr_calories))

        # 4. ML Model 1: Calorie Prediction
        le_gender = models["le_gender"]
        le_goal = models["le_goal"]
        calorie_model = models["calorie_model"]

        gender_enc = le_gender.transform([gender])[0]
        goal_enc = le_goal.transform([goal])[0]

        cols_cal = ["Age", "Gender_enc", "Height_cm", "Weight_kg", "BMI", "Workout_Hours_Per_Day", "Sleep_Hours", "Daily_Steps", "Goal_enc"]
        X_user_cal = pd.DataFrame([[age, gender_enc, height, weight, round(bmi, 2), workout_hours, sleep, steps, goal_enc]], columns=cols_cal)
        ml_calories = int(calorie_model.predict(X_user_cal)[0])

        # 5. ML Model 2: Workout Recommendation
        workout_model = models["workout_model"]
        le_workout = models["le_workout"]

        cols_wk = ["Age", "Gender_enc", "BMI", "Workout_Hours_Per_Day", "Daily_Steps", "Goal_enc"]
        X_user_wk = pd.DataFrame([[age, gender_enc, round(bmi, 2), workout_hours, steps, goal_enc]], columns=cols_wk)
        workout_enc = workout_model.predict(X_user_wk)[0]
        workout_pred = le_workout.inverse_transform([workout_enc])[0]

        workout_text_map = {
            "Strength Training": "Strength Training\n- Bench Press\n- Squats\n- Deadlift\n- Shoulder Press",
            "Cardio + HIIT":     "Fat Loss Workout\n- Running\n- HIIT\n- Cycling\n- Jump Rope",
            "Mixed Fitness":     "Maintenance Workout\n- Pushups\n- Pullups\n- Walking\n- Light Cardio",
        }
        workout_display = workout_text_map.get(workout_pred, workout_pred)

        # Medical warnings override/add-on
        medical_warn = {
            "Hypertension": "⚠️ Avoid heavy lifting & intense HIIT. Focus on low-impact cardio.",
            "Diabetes":     "⚠️ Post-meal walks recommended. Monitor blood sugar before/after workouts.",
            "Asthma":       "⚠️ Warm up thoroughly. Keep inhaler nearby. Avoid high-pollution outdoor exercise.",
        }
        warning = medical_warn.get(medical, "")

        # 6. ML Model 3: Diet Recommendation (Cosine Similarity)
        df_orig = models["df_original"]
        cv = models["cv"]

        user_feature = f"{goal}_{diet_pref}_{medical}"
        user_vec = cv.transform([user_feature])
        cv_matrix = cv.transform(df_orig["combined_features"])
        user_sim = cosine_similarity(user_vec, cv_matrix)[0]
        top_idx = user_sim.argsort()[::-1][:10]
        meal_pred = df_orig.iloc[top_idx]["Meal_Plan"].value_counts().idxmax()

        diet_text_map = {
            ("Bulk",    "Vegetarian"):   "Veg Bulk Diet\n- Paneer\n- Milk\n- Rice\n- Banana\n- Peanut Butter",
            ("Bulk",    "High Protein"): "Non-Veg Bulk Diet\n- Chicken\n- Eggs\n- Rice\n- Fish\n- Oats",
            ("Bulk",    "Balanced"):     "Non-Veg Bulk Diet\n- Chicken\n- Eggs\n- Rice\n- Fish\n- Oats",
            ("Bulk",    "Keto"):         "Keto Bulk\n- Eggs\n- Cheese\n- Beef\n- Avocado\n- Nuts",
            ("Bulk",    "Low Carb"):     "Low Carb Bulk\n- Chicken\n- Eggs\n- Paneer\n- Nuts\n- Broccoli",
            ("Cut",     "Vegetarian"):   "Veg Fat Loss Diet\n- Salad\n- Oats\n- Fruits\n- Green Tea",
            ("Cut",     "High Protein"): "Non-Veg Fat Loss Diet\n- Chicken Breast\n- Boiled Eggs\n- Vegetables\n- Soup",
            ("Cut",     "Balanced"):     "Non-Veg Fat Loss Diet\n- Chicken Breast\n- Boiled Eggs\n- Vegetables\n- Soup",
            ("Cut",     "Keto"):         "Keto Cut\n- Egg Whites\n- Fish\n- Spinach\n- Avocado\n- Olive Oil",
            ("Cut",     "Low Carb"):     "Low Carb Cut\n- Tuna\n- Cucumber\n- Cottage Cheese\n- Almonds",
            ("Maintain","Vegetarian"):   "Veg Maintenance\n- Dal\n- Roti\n- Sabzi\n- Curd\n- Fruits",
            ("Maintain","High Protein"): "High Protein Maintenance\n- Eggs\n- Chicken\n- Dal\n- Milk\n- Paneer",
            ("Maintain","Balanced"):     "Balanced Diet\n- Dal\n- Roti\n- Sabzi\n- Rice\n- Curd",
            ("Maintain","Keto"):         "Keto Maintain\n- Eggs\n- Avocado\n- Cheese\n- Nuts\n- Low-carb Veggies",
            ("Maintain","Low Carb"):     "Low Carb Maintain\n- Paneer\n- Eggs\n- Cauliflower\n- Almonds\n- Salad",
        }
        diet_display = diet_text_map.get((goal, diet_pref), f"Recommended: {meal_pred}")

        # 7. Macros
        protein_g = int(weight * (2.0 if goal == "Bulk" else 1.6))
        fat_g = int(ml_calories * 0.25 / 9)
        carb_g = max(0, int((ml_calories - protein_g * 4 - fat_g * 9) / 4))

        # 8. LSTM Weight Progress simulation
        lstm_scaler = models["lstm_scaler"]
        weight_history = models["weight_history"]
        
        scaled_history = lstm_scaler.transform(weight_history.reshape(-1, 1)).flatten()
        predicted_s = float(np.mean(scaled_history[-3:]) * 0.98)   # slight downtrend simulated
        lstm_next = round(float(lstm_scaler.inverse_transform([[predicted_s]])[0][0]), 2)
        
        # 4-week projection
        weekly_factors = {
            "Bulk": [0.5, 0.6, 0.4, 0.7],
            "Cut": [-0.8, -0.7, -0.9, -0.6],
            "Maintain": [0.0, -0.1, 0.1, 0.0]
        }
        wts_proj = [weight]
        for val in weekly_factors[goal]:
            wts_proj.append(round(wts_proj[-1] + val, 1))

        # Build response
        response = {
            "name": name,
            "bmi": round(bmi, 2),
            "bmi_status": bmi_status,
            "ml_calories": ml_calories,
            "bmr_calories": bmr_calories,
            "protein_g": protein_g,
            "carb_g": carb_g,
            "fat_g": fat_g,
            "sleep_status": "Good" if sleep >= 7 else "Low",
            "sleep_hours": sleep,
            "steps": steps,
            "workout_hours": workout_hours,
            "workout_plan": workout_pred,
            "workout_display": workout_display,
            "meal_plan": meal_pred,
            "diet_display": diet_display,
            "warning": warning,
            "weight_history": weight_history.tolist(),
            "lstm_next_weight": lstm_next,
            "projection_weeks": ["Start", "Week 1", "Week 2", "Week 3", "Week 4"],
            "projection_weights": wts_proj
        }
        
        return jsonify(response), 200

    except Exception as e:
        logger.error("Error during prediction request: %s", str(e), exc_info=True)
        return jsonify({"error": "An internal server error occurred", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
