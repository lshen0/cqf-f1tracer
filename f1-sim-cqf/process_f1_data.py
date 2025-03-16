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

    # ✅ Standardize overtaker names
    last_name_to_full_name = {name.split()[-1]: name for name in drivers["Driver"]}
    overtakes["Overtaker"] = overtakes["Overtaker"].map(last_name_to_full_name)

    # ✅ Compute overtake stats
    overtake_metrics = overtakes.groupby("Overtaker").agg(
        total_overtakes=("Overtaker", "count")
    ).reset_index()
    overtake_metrics.rename(columns={"Overtaker": "driver"}, inplace=True)

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

print("✅ Finished processing data for all 2020 races!")
