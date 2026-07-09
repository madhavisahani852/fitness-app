import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.feature_extraction.text import CountVectorizer

def train_and_save():
    # Setup paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir)
    dataset_path = os.path.join(root_dir, "AI_Fitness_Raw_Dataset.xlsx")
    models_dir = os.path.join(base_dir, "models")
    
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)

    print(f"Loading dataset from: {dataset_path}")
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    # Load and clean dataset
    df = pd.read_excel(dataset_path)
    df["Medical_Condition"] = df["Medical_Condition"].fillna("None")
    df.dropna(inplace=True)
    df_original = df.copy()

    # Fit Label Encoders
    le_gender = LabelEncoder()
    le_goal = LabelEncoder()
    le_workout = LabelEncoder()
    le_meal = LabelEncoder()
    le_diet = LabelEncoder()
    le_medical = LabelEncoder()

    df["Gender_enc"] = le_gender.fit_transform(df["Gender"])
    df["Goal_enc"] = le_goal.fit_transform(df["Fitness_Goal"])
    df["Workout_enc"] = le_workout.fit_transform(df["Workout_Recommendation"])
    df["Meal_enc"] = le_meal.fit_transform(df["Meal_Plan"])
    df["Diet_enc"] = le_diet.fit_transform(df["Dietary_Preference"])
    df["Medical_enc"] = le_medical.fit_transform(df["Medical_Condition"])

    # 1. Calorie Prediction Model (Linear Regression)
    print("Training Calorie Prediction Model...")
    X_cal = df[["Age", "Gender_enc", "Height_cm", "Weight_kg", "BMI",
                "Workout_Hours_Per_Day", "Sleep_Hours", "Daily_Steps", "Goal_enc"]]
    y_cal = df["Recommended_Calories"]
    
    X_cal_train, X_cal_test, y_cal_train, y_cal_test = train_test_split(
        X_cal, y_cal, test_size=0.2, random_state=42
    )
    
    calorie_model = LinearRegression()
    calorie_model.fit(X_cal_train, y_cal_train)
    
    # 2. Workout Recommendation Model (Random Forest)
    print("Training Workout Recommendation Model...")
    X_wk = df[["Age", "Gender_enc", "BMI", "Workout_Hours_Per_Day", "Daily_Steps", "Goal_enc"]]
    y_wk = df["Workout_enc"]
    
    X_wk_train, X_wk_test, y_wk_train, y_wk_test = train_test_split(
        X_wk, y_wk, test_size=0.2, random_state=42
    )
    
    workout_model = RandomForestClassifier(n_estimators=100, random_state=42)
    workout_model.fit(X_wk_train, y_wk_train)

    # 3. Diet Recommendation (CountVectorizer & Cosine Similarity)
    print("Fitting CountVectorizer for Diet Recommendation...")
    df_original["combined_features"] = (
        df_original["Fitness_Goal"] + "_" +
        df_original["Dietary_Preference"] + "_" +
        df_original["Medical_Condition"]
    )
    cv = CountVectorizer(analyzer="word", token_pattern=r"[^\s]+")
    cv.fit(df_original["combined_features"])

    # 4. Progress Tracker (LSTM Scaler & Weight History simulation)
    print("Fitting MinMaxScaler for Progress Tracker...")
    weight_history = np.array([85, 84, 83, 82, 81, 80, 79, 78, 77, 76], dtype=float)
    lstm_scaler = MinMaxScaler()
    lstm_scaler.fit(weight_history.reshape(-1, 1))

    # Save artifacts
    print(f"Saving artifacts to: {models_dir}")
    joblib.dump(calorie_model, os.path.join(models_dir, "calorie_model.pkl"))
    joblib.dump(workout_model, os.path.join(models_dir, "workout_model.pkl"))
    joblib.dump(le_gender, os.path.join(models_dir, "le_gender.pkl"))
    joblib.dump(le_goal, os.path.join(models_dir, "le_goal.pkl"))
    joblib.dump(le_workout, os.path.join(models_dir, "le_workout.pkl"))
    joblib.dump(cv, os.path.join(models_dir, "cv.pkl"))
    joblib.dump(df_original, os.path.join(models_dir, "df_original.pkl"))
    joblib.dump(lstm_scaler, os.path.join(models_dir, "lstm_scaler.pkl"))
    joblib.dump(weight_history, os.path.join(models_dir, "weight_history.pkl"))
    
    print("All models and preprocessing artifacts saved successfully!")

if __name__ == "__main__":
    train_and_save()
