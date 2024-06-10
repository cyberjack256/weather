

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

# Set up logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Set the base directory relative to the script location
base_dir = os.path.dirname(__file__)

def load_config() -> Dict[str, str]:
    """
    Load and validate the configuration from the config.json file.
    Returns:
        Dict[str, str]: The loaded configuration.
    """
    config_path = os.path.join(base_dir, 'config.json')
    try:
        with open(config_path, 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        logging.error("Configuration file not found.")
        raise
    except json.JSONDecodeError:
        logging.error("Error decoding JSON from the configuration file.")
        raise

    if any(value == "REPLACEME" for value in config.values()):
        raise ValueError("Please replace all 'REPLACEME' fields in the config file.")

    return config

def get_timezone(latitude: float, longitude: float) -> ZoneInfo:
    """
    Get the timezone for a given latitude and longitude.
    Args:
        latitude (float): The latitude.
        longitude (float): The longitude.
    Returns:
        ZoneInfo: The timezone information.
    """
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=latitude, lng=longitude)
    if tz_name:
        return ZoneInfo(tz_name)
    else:
        raise Exception("Could not determine the timezone.")

def fetch_weather_data(latitude: float, longitude: float, date_start: str, date_end: str, units: str) -> pd.DataFrame:
    """
    Fetch weather data for the specified location and date range.
    Args:
        latitude (float): The latitude of the location.
        longitude (float): The longitude of the location.
        date_start (str): The start date in 'YYYY-MM-DD' format.
        date_end (str): The end date in 'YYYY-MM-DD' format.
        units (str): The units of measurement, either 'imperial' or 'metric'.
    Returns:
        pd.DataFrame: The fetched weather data.
    """
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

def generate_log_lines(weather_data: pd.DataFrame, sun_and_moon_info: Dict[str, Any], encounter_id: str, alias: str, config: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Generate log lines from weather data and sun/moon information.
    Args:
        weather_data (pd.DataFrame): The weather data.
        sun_and_moon_info (Dict[str, Any]): The sun and moon information.
        encounter_id (str): The encounter ID.
        alias (str): The alias.
        config (Dict[str, str]): The configuration dictionary.
    Returns:
        List[Dict[str, Any]]: The generated log lines.
    """
    logging.info("Generating log lines...")
    log_lines = []
    for time, row in weather_data.iterrows():
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
            "moon_phase": sun_and_moon_info["moon_phase"],
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
        log_lines.append(log_entry)
    logging.info("Generated log lines:")
    logging.info(log_lines)
    return log_lines

def send_to_logscale(logscale_api_url: str, logscale_api_token: str, data: List[Dict[str, Any]]) -> Tuple[int, str]:
    """
    Send data to LogScale using the case study token.
    Args:
        logscale_api_url (str): The LogScale API URL.
        logscale_api_token (str): The LogScale API token.
        data (List[Dict[str, Any]]): The data to send.
    Returns:
        Tuple[int, str]: The HTTP status code and response text.
    """
    logging.info("Sending data to LogScale...")
    headers = {
        "Authorization": f"Bearer {logscale_api_token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(logscale_api_url, json=data, headers=headers)
        response.raise_for_status()
        logging.info(f"Response from LogScale: Status Code: {response.status_code}, Response: {response.text}")
        return response.status_code, response.text
    except requests.RequestException as e:
        logging.error(f"Failed to send data to LogScale: {e}")
        raise

def main():
    """Main function to load configuration, generate events, and send them to LogScale."""
    try:
        config = load_config()
        latitude = float(config['latitude'])
        longitude = float(config['longitude'])
        date_start = config['date_start']
        date_end = config['date_end']
        alias = config['alias']
        encounter_id = config['encounter_id']
        units = config.get('units', 'metric')

        # Get timezone
        timezone = get_timezone(latitude, longitude)
        logging.info(f"Timezone: {timezone}")

        # Fetch sun and moon data
        city = LocationInfo(config['city_name'], config['country_name'], timezone, latitude, longitude)
        date_specified = datetime.now()
        s = sun(city.observer, date=date_specified, tzinfo=city.timezone)
        moon_phase_value = phase(date_specified)
        sun_and_moon_info = {
            'sun_info': {
                'dawn': s['dawn'].isoformat(),
                'sunrise': s['sunrise'].isoformat(),
                'noon': s['noon'].isoformat(),
                'sunset': s['sunset'].isoformat(),
                'dusk': s['dusk'].isoformat(),
            },
            'moon_phase': moon_phase_value
        }
        logging.info("Sun and moon information:")
        logging.info(sun_and_moon_info)

        # Fetch weather data
        weather_data = fetch_weather_data(latitude, longitude, date_start, date_end, units)

        # Generate log lines
        log_lines = generate_log_lines(weather_data, sun_and_moon_info, encounter_id, alias, config)

        # Send log lines to LogScale
        structured_data = [{"tags": {"host": "weatherhost", "source": "weatherdata"}, "events": [{"timestamp": event['@timestamp'], "attributes": event} for event in log_lines]}]
        status_code, response_text = send_to_logscale(config['logscale_api_url'], config['logscale_api_token_case_study'], structured_data)
        logging.info(f"Status Code: {status_code}, Response: {response_text}")
    except Exception as e:
        logging.error("An error occurred: ", exc_info=True)
        print(e)

if __name__ == "__main__":
    main()

