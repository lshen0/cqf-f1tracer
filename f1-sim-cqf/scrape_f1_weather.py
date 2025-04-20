import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Mapping from CSV race names to Wikipedia-friendly names
race_name_mapping = {
    "Austria": "Austrian",
    "Styria": "Styrian",
    "Hungary": "Hungarian",
    "Great Britain": "British",
    "70th Anniversary": "70th_Anniversary_Grand_Prix",  # Special case: No "2020"
    "Spain": "Spanish",
    "Belgium": "Belgian",
    "Italy": "Italian",
    "Tuscany": "Tuscan",
    "Russia": "Russian",
    "Eifel": "Eifel",
    "Portugal": "Portuguese",
    "Emilia Romagna": "Emilia_Romagna",
    "Turkey": "Turkish",
    "Bahrain": "Bahrain",
    "Sakhir": "Sakhir",
    "Abu Dhabi": "Abu_Dhabi"
}

def get_race_weather(race_name):
    """Fetches weather details from Wikipedia for a given F1 race."""
    wiki_race_name = race_name_mapping.get(race_name, race_name)  # Fix Wikipedia formatting
    
    # Handle the special case for the 70th Anniversary Grand Prix
    if race_name == "70th Anniversary":
        url = f"https://en.wikipedia.org/wiki/{wiki_race_name}"
    else:
        url = f"https://en.wikipedia.org/wiki/2020_{wiki_race_name.replace(' ', '_')}_Grand_Prix"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Failed to fetch Wikipedia page for {race_name}: HTTP {response.status_code}")
            return "Unknown"

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the infobox
        race_info = soup.find("table", {"class": "infobox infobox-table vevent"})  # ✅ Corrected table class
        if race_info is None:
            print(f"⚠️ No race info table found for {race_name}, skipping...")
            return "Unknown"

        # Extract weather information
        for row in race_info.find_all("tr"):
            header = row.find("th", {"class": "infobox-label"})
            if header and "Weather" in header.text:
                weather_info = row.find("td", {"class": "infobox-data"})
                return weather_info.text.strip() if weather_info else "Unknown"

    except Exception as e:
        print(f"⚠️ Error fetching weather for {race_name}: {e}")

    return "Unknown"

# Load the race calendar
calendar_df = pd.read_csv("data/2020_data/formula1_2020season_calendar.csv")

# Fetch weather for each race (add delay to prevent Wikipedia rate limits)
weather_data = []
for race_name in calendar_df["GP Name"]:
    weather = get_race_weather(race_name)
    weather_data.append({"race_name": race_name, "weather": weather})
    time.sleep(1)  # Wait to avoid hitting Wikipedia's request limits

# Convert to DataFrame & Save
weather_df = pd.DataFrame(weather_data)
weather_df.to_csv("data/2020_data/weather_data.csv", index=False)

print("✅ Weather data successfully saved as data/2020_data/weather_data.csv")
