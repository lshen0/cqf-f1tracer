import fastf1
import pandas as pd
import os

# Enable FastF1 cache
fastf1.Cache.enable_cache('f1_cache')

# Define season and output folder
season_year = 2020
output_folder = "data/2020_lap_data/"

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Load the race calendar to get all rounds
calendar_df = pd.read_csv("f1-sim-cqf/data/2020_data/formula1_2020season_calendar.csv")

# Loop through all races in the season
for _, race in calendar_df.iterrows():
    race_name = race["GP Name"]
    race_round = race["Round"]  # Assuming there's a column for race round

    print(f"🔹 Processing {race_name} (Round {race_round})...")

    try:
        # Load session data for the race
        session = fastf1.get_session(season_year, race_round, 'R')
        session.load()

        lap_data = []
        for driver in session.drivers:
            driver_laps = session.laps.pick_driver(driver)
            for _, lap in driver_laps.iterrows():
                lap_data.append({
                    "driver": driver,
                    "lap_number": lap["LapNumber"],
                    "lap_time": lap["LapTime"].total_seconds() if pd.notnull(lap["LapTime"]) else None,
                    "position": lap["Position"],
                    "race": race_name  # Add race name to track which race this data is from
                })

        # Save lap data for this race
        lap_df = pd.DataFrame(lap_data)
        lap_df.to_csv(f"{output_folder}/{race_name}_lap_data.csv", index=False)
        print(f"✅ Lap data saved for {race_name}!")

    except Exception as e:
        print(f"⚠️ Failed to process {race_name}: {e}")

print("✅ Finished extracting lap data for all 2020 races!")
