"""
import pandas as pd
import os

print("🔹 Script started...")

# Define folder paths
lap_data_folder = "f1-sim-cqf/data/2020_data/2020_lap_data/"  # ✅ Corrected path
data_folder = "f1-sim-cqf/data/2020_data/"
output_folder = "f1-sim-cqf/data/processed/"

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Load static datasets
game_ratings = pd.read_csv(os.path.join(data_folder, "f1_2020_videogame_driver_ratings_jan2021.csv"))
drivers = pd.read_csv(os.path.join(data_folder, "formula1_2020season_drivers.csv"))
overtakes = pd.read_csv(os.path.join(data_folder, "2020 Overtakes.csv"))
weather_data = pd.read_csv(os.path.join(data_folder, "weather_data.csv"))  # Weather from Wikipedia
calendar_df = pd.read_csv(os.path.join(data_folder, "formula1_2020season_calendar.csv"))  # Race schedule

# ✅ Fix column names for game ratings (match actual dataset)
game_ratings["aggressiveness"] = game_ratings["Racecraft"] / 100
game_ratings["defensive_ability"] = game_ratings["Awareness"] / 100
game_ratings["stamina"] = game_ratings["Experience"] / 100
game_ratings = game_ratings[["Driver", "aggressiveness", "defensive_ability", "stamina"]]

# ✅ Clean driver names
drivers["Driver"] = drivers["Driver"].str.strip()
game_ratings["Driver"] = game_ratings["Driver"].str.strip()
overtakes["Overtaker"] = overtakes["Overtaker"].str.strip()

# ✅ Process each race separately
for lap_data_file in os.listdir(lap_data_folder):
    if not lap_data_file.endswith(".csv"):
        continue

    # Extract the race name from the filename
    race_name = lap_data_file.replace("_lap_data.csv", "").replace("_", " ")
    
    # Find the corresponding race info from the calendar
    race_info = calendar_df[calendar_df["GP Name"].str.contains(race_name, case=False, na=False)]

    if race_info.empty:
        print(f"⚠️ No matching race info found for {race_name}, skipping...")
        continue

    race_number = race_info["Round"].values[0]  # ✅ Corrected column name for race round

    print(f"🔹 Processing data for {race_name} (Round {race_number})...")

    # ✅ Load lap data for this race
    lap_data = pd.read_csv(os.path.join(lap_data_folder, lap_data_file))
    lap_data.dropna(subset=["driver", "lap_time"], inplace=True)
    lap_data["driver"] = lap_data["driver"].astype(str).str.strip()

    # ✅ Map Driver Numbers to Full Names
    driver_id_to_name = dict(zip(drivers["Number"].astype(str), drivers["Driver"]))
    lap_data["driver"] = lap_data["driver"].map(driver_id_to_name)

    # ✅ Standardize overtaker names (only last names exist in overtakes dataset)
    overtakes["Overtaker"] = overtakes["Overtaker"].str.strip()

    # ✅ Create a mapping of last names to full names from the drivers dataset
    last_name_to_full_name = {name.split()[-1]: name for name in drivers["Driver"]}

    # ✅ Perform partial string matching (map last names to full names)
# ✅ Ensure names match even if spacing/capitalization is slightly off
    overtakes["Overtaker"] = overtakes["Overtaker"].apply(lambda x: next((full_name for last, full_name in last_name_to_full_name.items() if last.lower() == x.lower()), x))

    # ✅ Filter overtakes only for the current race
    race_overtakes = overtakes[overtakes["Race"].str.contains(race_name, case=False, na=False)]

    # ✅ Compute overtake stats per driver
    overtake_metrics = race_overtakes.groupby("Overtaker").agg(
        total_overtakes=("Overtaker", "count")
    ).reset_index()

# ✅ Rename "Overtaker" to "driver" for merging
    overtake_metrics.rename(columns={"Overtaker": "driver"}, inplace=True)

    # ✅ Ensure `final_df` exists before merging overtakes
    final_df = lap_data.copy()

    # ✅ Merge game ratings first
    final_df = final_df.merge(game_ratings, left_on="driver", right_on="Driver", how="left").drop(columns=["Driver"])

    # ✅ Merge overtakes data with final dataset
    final_df = final_df.merge(overtake_metrics, on="driver", how="left")

    # ✅ Ensure missing values are filled with 0 (if no overtakes)
    final_df["total_overtakes"] = final_df["total_overtakes"].fillna(0)


    # ✅ Merge game ratings
    final_df = lap_data.merge(game_ratings, left_on="driver", right_on="Driver", how="left").drop(columns=["Driver"])
    final_df = final_df.merge(overtake_metrics, on="driver", how="left")

    # ✅ Merge weather data for the race
    race_weather = weather_data[weather_data["race_name"].str.contains(race_name, case=False, na=False)]["weather"].values
    final_df["weather"] = race_weather[0] if len(race_weather) > 0 else "Unknown"

    # ✅ Fill Missing Values with 0
    final_df.fillna(0, inplace=True)

    # ✅ Save Processed Data with Year, Race Number & Name
    output_filename = f"2020_{str(race_number).zfill(2)}_{race_name.replace(' ', '_')}_processed.csv"
    output_file = os.path.join(output_folder, output_filename)
    final_df.to_csv(output_file, index=False)

    print(f"✅ Processed dataset saved as {output_filename}!")

print("✅ Finished processing data for all 2020 races!")"
"""

import pandas as pd
import os
from datetime import datetime

print("🔹 Script started...")

# === Define folder paths ===
lap_data_folder = "f1-sim-cqf/data/2020_data/2020_lap_data/"
data_folder = "f1-sim-cqf/data/2020_data/"
output_folder = "f1-sim-cqf/data/processed/"
os.makedirs(output_folder, exist_ok=True)

# === Load static datasets ===
game_ratings = pd.read_csv(os.path.join(data_folder, "f1_2020_videogame_driver_ratings_jan2021.csv"))
drivers = pd.read_csv(os.path.join(data_folder, "formula1_2020season_drivers.csv"))
overtakes = pd.read_csv(os.path.join(data_folder, "2020 Overtakes.csv"))
weather_data = pd.read_csv(os.path.join(data_folder, "weather_data.csv"))
calendar_df = pd.read_csv(os.path.join(data_folder, "formula1_2020season_calendar.csv"))

# === Normalize/clean names ===
drivers["Driver"] = drivers["Driver"].str.strip()
game_ratings["Driver"] = game_ratings["Driver"].str.strip()
overtakes["Overtaker"] = overtakes["Overtaker"].str.strip()

# === Normalize game ratings ===
game_ratings["aggressiveness"] = game_ratings["Racecraft"] / 100
game_ratings["defensive_ability"] = game_ratings["Awareness"] / 100
game_ratings["stamina"] = game_ratings["Experience"] / 100
game_ratings = game_ratings[["Driver", "aggressiveness", "defensive_ability", "stamina"]]

# === Team data mapping ===
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

# Add team features to drivers
drivers["championships"] = drivers["Team"].map(lambda t: team_data.get(t, {}).get("championships", 0))
drivers["employees"] = drivers["Team"].map(lambda t: team_data.get(t, {}).get("employees", 0))
drivers["engine_manufacturer"] = drivers["Team"].map(lambda t: team_data.get(t, {}).get("engine_manufacturer", 0))

# === Calculate driver age from DOB ===
today = datetime(2020, 7, 1)  # Approximate mid-2020
drivers["Age"] = pd.to_datetime(drivers["Date of Birth"], dayfirst=True).apply(lambda dob: (today - dob).days // 365)

# === Process each race ===
for lap_data_file in os.listdir(lap_data_folder):
    if not lap_data_file.endswith(".csv"):
        continue

    race_name = lap_data_file.replace("_lap_data.csv", "").replace("_", " ")
    race_info = calendar_df[calendar_df["GP Name"].str.contains(race_name, case=False, na=False)]

    if race_info.empty:
        print(f"⚠️ No matching race info found for {race_name}, skipping...")
        continue

    race_number = race_info["Round"].values[0]
    print(f"🔹 Processing {race_name} (Round {race_number})...")

    lap_data = pd.read_csv(os.path.join(lap_data_folder, lap_data_file))
    lap_data.dropna(subset=["driver", "lap_time"], inplace=True)
    lap_data["driver"] = lap_data["driver"].astype(str).str.strip()

    # Map driver numbers to full names
    driver_map = dict(zip(drivers["Number"].astype(str), drivers["Driver"]))
    lap_data["driver"] = lap_data["driver"].map(driver_map)

    # Standardize overtaker names
    last_name_map = {d.split()[-1]: d for d in drivers["Driver"]}
    overtakes["Overtaker"] = overtakes["Overtaker"].apply(
        lambda x: next((full for last, full in last_name_map.items() if last.lower() == x.lower()), x)
    )
    race_overtakes = overtakes[overtakes["Race"].str.contains(race_name, case=False, na=False)]

    overtake_stats = race_overtakes.groupby("Overtaker").agg(
        total_overtakes=("Overtaker", "count")
    ).reset_index().rename(columns={"Overtaker": "driver"})

    # Merge everything
    final_df = lap_data.copy()
    final_df = final_df.merge(game_ratings, left_on="driver", right_on="Driver", how="left").drop(columns=["Driver"])
    final_df = final_df.merge(overtake_stats, on="driver", how="left")
    final_df["total_overtakes"] = final_df["total_overtakes"].fillna(0)

    # Merge driver-level metadata
    final_df = final_df.merge(drivers[["Driver", "championships", "employees", "engine_manufacturer", "Age"]],
                              left_on="driver", right_on="Driver", how="left").drop(columns=["Driver"])

    # Merge weather
    weather_match = weather_data[weather_data["race_name"].str.contains(race_name, case=False, na=False)]
    final_df["weather"] = weather_match["weather"].values[0] if not weather_match.empty else "Unknown"

    # Final cleanup
    final_df.fillna(0, inplace=True)

    # Save!
    outname = f"2020_{str(race_number).zfill(2)}_{race_name.replace(' ', '_')}_processed.csv"
    final_df.to_csv(os.path.join(output_folder, outname), index=False)
    print(f"✅ Saved: {outname}")

print("✅ Done processing all races.")

