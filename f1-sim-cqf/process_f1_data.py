import pandas as pd
import os

print("🔹 Script started...")

# Define folder paths
data_folder = "data/2020_data/"
output_folder = "data/processed/"

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# === Load Data ===
lap_data = pd.read_csv(data_folder + "lap_data_2020.csv")
game_ratings = pd.read_csv(data_folder + "f1_2020_videogame_driver_ratings_jan2021.csv")
drivers = pd.read_csv(data_folder + "formula1_2020season_drivers.csv")
overtakes = pd.read_csv(data_folder + "2020 Overtakes.csv")
weather_data = pd.read_csv(data_folder + "weather_data.csv")  # 🔹 Load weather data from Wikipedia scraping

# === Step 1: Clean Driver Names ===
drivers["Driver"] = drivers["Driver"].str.strip()
game_ratings["Driver"] = game_ratings["Driver"].str.strip()
overtakes["Overtaker"] = overtakes["Overtaker"].str.strip()

# === Step 2: Clean Lap Data ===
lap_data.dropna(subset=["driver", "lap_time"], inplace=True)  # Remove incomplete laps
lap_data["driver"] = lap_data["driver"].astype(str).str.strip()

# === Step 3: Map Driver Numbers to Full Names ===
driver_id_to_name = dict(zip(drivers["Number"].astype(str), drivers["Driver"]))
lap_data["driver"] = lap_data["driver"].map(driver_id_to_name)

# === Step 4: Clean and Merge Overtakes Data ===
# Standardize overtaker names (match last name to full name)
last_name_to_full_name = {name.split()[-1]: name for name in drivers["Driver"]}
overtakes["Overtaker"] = overtakes["Overtaker"].map(last_name_to_full_name)

# Compute overtake stats
overtake_metrics = overtakes.groupby("Overtaker").agg(
    total_overtakes=("Overtaker", "count")
).reset_index()

# Rename "Overtaker" to "driver" for merging
overtake_metrics.rename(columns={"Overtaker": "driver"}, inplace=True)

# === Step 5: Clean and Normalize Game Ratings ===
game_ratings["aggressiveness"] = game_ratings["Racecraft"] / 100
game_ratings["defensive_ability"] = game_ratings["Awareness"] / 100
game_ratings["stamina"] = game_ratings["Experience"] / 100
game_ratings = game_ratings[["Driver", "aggressiveness", "defensive_ability", "stamina"]]

# === Step 6: Integrate Team Data ===
team_data = {
    "Mercedes": {"championships": 8, "employees": 1200, "engine_manufacturer": 1},
    "Red Bull Racing": {"championships": 4, "employees": 1000, "engine_manufacturer": 1},
    "Ferrari": {"championships": 16, "employees": 700, "engine_manufacturer": 1},
    "McLaren": {"championships": 8, "employees": 900, "engine_manufacturer": 0},
    "Alpine (Renault)": {"championships": 2, "employees": 950, "engine_manufacturer": 1},
    "Aston Martin": {"championships": 0, "employees": 500, "engine_manufacturer": 0},
    "AlphaTauri": {"championships": 0, "employees": 400, "engine_manufacturer": 0},
    "Alfa Romeo": {"championships": 0, "employees": 300, "engine_manufacturer": 0},
    "Haas": {"championships": 0, "employees": 250, "engine_manufacturer": 0},
    "Williams": {"championships": 9, "employees": 700, "engine_manufacturer": 0}
}

# Add team data to drivers
drivers["championships"] = drivers["Team"].map(lambda x: team_data.get(x, {}).get("championships", 0))
drivers["employees"] = drivers["Team"].map(lambda x: team_data.get(x, {}).get("employees", 0))
drivers["engine_manufacturer"] = drivers["Team"].map(lambda x: team_data.get(x, {}).get("engine_manufacturer", 0))

# Merge team data into lap dataset
lap_data = lap_data.merge(drivers[["Driver", "Team", "championships", "employees", "engine_manufacturer"]],
                          left_on="driver", right_on="Driver", how="left").drop(columns=["Driver"])

# === Step 7: Merge All Data ===
final_df = lap_data.merge(game_ratings, left_on="driver", right_on="Driver", how="left").drop(columns=["Driver"])
final_df = final_df.merge(overtake_metrics, on="driver", how="left")

# === Step 8: Merge Weather Data ===
final_df["weather"] = "Sunny"
# === Step 9: Fill Missing Values with 0 ===
final_df.fillna(0, inplace=True)

# === Step 10: Save Processed Data ===
output_file = output_folder + "final_f1_dataset.csv"
final_df.to_csv(output_file, index=False)

print(f"✅ Final dataset saved as {output_file}")
