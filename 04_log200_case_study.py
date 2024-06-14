import json
import os
from astral import LocationInfo
from astral.sun import sun
from astral.moon import phase
from datetime import datetime, timedelta
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo
import requests
from meteostat import Point, Daily, Stations
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Set the base directory relative to the script location
base_dir = os.path.dirname(__file__)
config_path = os.path.join(base_dir, 'config.json')

def load_config():
    with open(config_path, 'r') as file:
        return json.load(file)

def save_config(config):
    with open(config_path, 'w') as file:
        json.dump(config, file, indent=4)

def prompt_for_value(prompt, hint):
    value = input(f"{prompt} ({hint}): ")
    return value

def validate_input(prompt, hint, validate_func):
    while True:
        value = prompt_for_value(prompt, hint)
        if validate_func(value):
            return value
        else:
            print(f"Invalid value. Please try again.")

def get_timezone(latitude: float, longitude: float) -> ZoneInfo:
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=latitude, lng=longitude)
    if tz_name:
        return ZoneInfo(tz_name)
    else:
        raise Exception("Could not determine the timezone.")

def fetch_weather_data(latitude: float, longitude: float, date_start: str, date_end: str, units: str) -> pd.DataFrame:
    logging.info("Fetching weather data...")
    location = Point(latitude, longitude)
    start = datetime.strptime(date_start, '%Y-%m-%d')
    end = datetime.strptime(date_end, '%Y-%m-%d')
    data = Daily(location, start, end)
    data = data.fetch()

    # Optional: enrich data with nearest weather station information
    stations = Stations()
    stations = stations.nearby(latitude, longitude)
    station = stations.fetch(1)
    if not station.empty:
        station_name = station.name.iloc[0]
        data['station_name'] = station_name

    # Replace NaN and infinite values with None to avoid JSON serialization issues
    data = data.replace([np.nan, np.inf, -np.inf], None)
    logging.info("Fetched weather data:")
    logging.info(data)
    return data

def normalize_moon_phase(phase_value):
    phase_value %= 1
    if phase_value < 0.125:
        return "New Moon"
    elif phase_value < 0.25:
        return "Waxing Crescent"
    elif phase_value < 0.375:
        return "First Quarter"
    elif phase_value < 0.5:
        return "Waxing Gibbous"
    elif phase_value < 0.625:
        return "Full Moon"
    elif phase_value < 0.75:
        return "Waning Gibbous"
    elif phase_value < 0.875:
        return "Last Quarter"
    else:
        return "Waning Crescent"

def generate_log_lines(weather_data: pd.DataFrame, sun_and_moon_info: Dict[str, Any], encounter_id: str, alias: str, config: Dict[str, str]) -> Dict[str, Any]:
    logging.info("Generating log lines...")
    time, row = next(weather_data.iterrows())
    log_entry = {
        "@timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "geo": {
            "city_name": config["city_name"],
            "country_name": config["country_name"],
            "location": {
                "lat": config["latitude"],
                "lon": config["longitude"]
            }
        },
        "observer": {
            "alias": alias,
            "id": encounter_id
        },
        "ecs": {
            "version": "1.12.0"
        },
        "moon": {
            "phase": sun_and_moon_info["moon_phase"],
            "description": sun_and_moon_info["moon_phase_desc"]
        },
        "weather": {
            "temperature": row["tavg"],
            "min_temperature": row["tmin"],
            "max_temperature": row["tmax"],
            "precipitation": row["prcp"],
            "snow": row["snow"],
            "wind": {
                "speed": row["wspd"],
                "direction": row["wdir"],
                "gust": row["wpgt"]
            },
            "pressure": row["pres"],
            "sunshine": row["tsun"],
            "station_name": row.get("station_name", "N/A")
        },
        "event": {
            "created": datetime.utcnow().isoformat() + "Z",
            "module": "weather",
            "dataset": "weather"
        },
        "sun": {
            "sunrise": sun_and_moon_info["sun_info"]["sunrise"],
            "noon": sun_and_moon_info["sun_info"]["noon"],
            "dusk": sun_and_moon_info["sun_info"]["dusk"],
            "sunset": sun_and_moon_info["sun_info"]["sunset"],
            "dawn": sun_and_moon_info["sun_info"]["dawn"]
        }
    }
    logging.info("Generated log line:")
    logging.info(log_entry)
    return log_entry

def send_to_logscale(logscale_api_url: str, logscale_api_token: str, data: Dict[str, Any]) -> Tuple[int, str]:
    logging.info("Sending data to LogScale...")
    headers = {
        "Authorization": f"Bearer {logscale_api_token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(logscale_api_url, json=[data], headers=headers)
        response.raise_for_status()
        logging.info(f"Response from LogScale: Status Code: {response.status_code}, Response: {response.text}")
        return response.status_code, response.text
    except requests.RequestException as e:
        logging.error(f"Failed to send data to LogScale: {e}")
        raise

def main():
    config = load_config()

    # Check and prompt for required values if missing
    if not config.get("alias"):
        config["alias"] = validate_input("Enter alias", "e.g., racing-jack", lambda x: bool(x))
    if not config.get("encounter_id"):
        config["encounter_id"] = validate_input("Enter encounter ID", "e.g., jt30", lambda x: bool(x))
    if not config.get("logscale_api_token_case_study"):
        config["logscale_api_token_case_study"] = validate_input("Enter LogScale API Token (Case Study)", "e.g., 7f51ecfe-71a5-4268-81d7-7f0c81c6105f", lambda x: bool(x))
    if not config.get("city_name"):
        config["city_name"] = validate_input("Enter city name", "e.g., Ann Arbor", lambda x: bool(x))
    if not config.get("country_name"):
        config["country_name"] = validate_input("Enter country name", "e.g., US", lambda x: bool(x))
    if not config.get("latitude"):
        config["latitude"] = validate_input("Enter latitude", "e.g., 42.2808", lambda x: bool(x))
    if not config.get("longitude"):
        config["longitude"] = validate_input("Enter longitude", "e.g., -83.7430", lambda x: bool(x))
    if not config.get("date_start"):
        config["date_start"] = validate_input("Enter start date", "YYYY-MM-DD", lambda x: bool(x))
    if not config.get("date_end"):
        config["date_end"] = validate_input("Enter end date", "YYYY-MM-DD", lambda x: bool(x))
    if not config.get("units"):
        config["units"] = validate_input("Enter units", "imperial or metric", lambda x: x in ["imperial", "metric"])

    save_config(config)

    latitude = float(config['latitude'])
    longitude = float(config['longitude'])
    date_start = config['date_start']
    date_end = config['date_end']
    alias = config['alias']
    encounter_id = config['encounter_id']
    units = config['units']
    token = config['logscale_api_token_case_study']

    # Get timezone
    timezone = get_timezone(latitude, longitude)
    logging.info(f"Timezone: {timezone}")

    # Fetch sun and moon data
    city = LocationInfo(config['city_name'], config['country_name'], timezone, latitude, longitude)
    date_specified = datetime.now()
    s = sun(city.observer, date=date_specified, tzinfo=city.timezone)
    moon_phase_value = phase(date_specified)
    moon_phase_desc = normalize_moon_phase(moon_phase_value)
    sun_and_moon_info = {
        'sun_info': {
            'dawn': s['dawn'].isoformat(),
            'sunrise': s['sunrise'].isoformat(),
            'noon': s['noon'].isoformat(),
            'sunset': s['sunset'].isoformat(),
            'dusk': s['dusk'].isoformat(),
        },
        'moon_phase': moon_phase_value,
        'moon_phase_desc': moon_phase_desc
    }
    logging.info("Sun and moon information:")
    logging.info(sun_and_moon_info)

    # Fetch weather data
    weather_data = fetch_weather_data(latitude, longitude, date_start, date_end, units)

    # Generate log line
    log_line = generate_log_lines(weather_data, sun_and_moon_info, encounter_id, alias, config)

    # Send log line to LogScale
    status_code, response_text = send_to_logscale(config['logscale_api_url'], token, log_line)
    logging.info(f"Status Code: {status_code}, Response: {response_text}")

    # Print out the log line and HTTP information
    print("Example Log Line:")
    print(json.dumps(log_line, indent=4))
    print("\nHTTP Information:")
    print(f"Status Code: {status_code}")
    print(f"Response: {response_text}")

    print("\nThe log format includes various fields such as '@timestamp', 'geo', 'observer', 'ecs', 'moon', 'weather', 'event', and 'sun'.")
    print("You can search your LogScale view using the following query:")
    print(f"observer.id={encounter_id} AND observer.alias={alias}")
    print(f"Adjust the time picker for the range: {date_start} to {date_end}")

if __name__ == "__main__":
    main()
