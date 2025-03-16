import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_cache')  # Enable caching for efficiency

season_year = 2020
race_round = 1  # Example: First race of the season (adjust as needed)
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
            "position": lap["Position"]
        })

lap_df = pd.DataFrame(lap_data)
lap_df.to_csv("lap_data_2020.csv", index=False)
print("Lap data saved!")
