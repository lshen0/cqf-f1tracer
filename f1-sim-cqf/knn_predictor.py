import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from scipy.spatial.distance import cosine

# === Step 1: Load All Processed Race CSVs ===
data_folder = "data/processed"
race_dfs = []

for filename in os.listdir(data_folder):
    if filename.endswith(".csv") and not filename.startswith("final_"):
        df = pd.read_csv(os.path.join(data_folder, filename))
        #print(f"📂 Loaded {filename}, shape: {df.shape}")
        df["source_race"] = filename  # Tag where this data came from
        race_dfs.append(df)

full_data = pd.concat(race_dfs, ignore_index=True)

# === Step 2: Select Features ===
features = [
    "lap_number", "position", "aggressiveness", "defensive_ability", "stamina",
    "total_overtakes", "Age", "championships", "employees", "engine_manufacturer"
]

# One-hot encode weather if it exists and has multiple values
if "weather" in full_data.columns:
    full_data = pd.get_dummies(full_data, columns=["weather"])
    features += [col for col in full_data.columns if col.startswith("weather_")]

X = full_data[features].values
lap_times = full_data["lap_time"].values

# === Step 3: Normalize Features ===
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

# === Step 4: Define Cosine Similarity KNN ===
def cosine_knn_predict(test_vector, X_train, y_train, k=5):
    similarities = np.array([1 - cosine(test_vector, x) for x in X_train])
    top_k_indices = similarities.argsort()[-k:][::-1]  # Top K most similar
    top_k_lap_times = y_train[top_k_indices]
    predicted_lap_time = np.mean(top_k_lap_times)
    return predicted_lap_time, top_k_indices

# === Step 5: Test with a Sample Vector ===
def predict_single(test_dict, k=5):
    test_df = pd.DataFrame([test_dict])
    test_df = test_df.reindex(columns=features, fill_value=0)
    test_vector = scaler.transform(test_df.values)[0]
    pred, idxs = cosine_knn_predict(test_vector, X_scaled, lap_times, k)
    print(f"🔮 Predicted lap time: {pred:.3f} seconds")
    print("Closest laps:")
    print(full_data.iloc[idxs][["driver", "lap_time", "position", "source_race"]])
    return pred

# === Example Usage ===
if __name__ == "__main__":
    test_vector = {
        "lap_number": 17,
        "position": 15,
        "aggressiveness": 0.68,
        "defensive_ability": 0.71,
        "stamina": 0.79,
        "total_overtakes": 3,
        "Age": 30,
        "championships": 8,
        "employees": 1200,
        "engine_manufacturer": 1,
        "weather_Sunny": 0,
        "weather_Wet": 1,
        "weather_Unknown": 0
    }

    predict_single(test_vector, k=5)
