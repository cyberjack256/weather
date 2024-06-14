import json
import os
import logging
import requests
from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun
from astral.moon import phase
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo
from meteostat import Point, Daily, Stations
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Set the base directory relative to the script location
base_dir = os.path.dirname(__file__)

CONFIG_FILE = 'config.json'
LOGSCALE_URL = 'https://cloud.us.humio.com/api/v1/ingest/humio-structured'

# Load and validate the configuration
def load_config():
    config_path = os.path.join(base_dir, CONFIG_FILE)
    with open(config_path, 'r') as file:
        config = json.load(file)
    return config

# Initialize TimezoneFinder
def get_timezone(latitude, longitude):
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=latitude, lng=longitude)
    if tz_name:
        return ZoneInfo(tz_name)
    else:
        raise Exception("Could not determine the timezone.")

# Fetch weather data for the specified date range
def fetch_weather_data(latitude, longitude, date_start, date_end):
    logging.debug("Fetching weather data...")
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
    logging.debug(f"Weather data fetched: {data}")
    return data

# Generate log lines
def generate_log_lines(weather_data, sun_and_moon_info, encounter_id, alias, config):
    logging.debug("Generating log lines...")
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
    logging.debug(f"Generated log lines: {log_lines}")
    return log_lines

# Send data to LogScale
def send_to_logscale(logscale_api_url, logscale_api_token, data):
    logging.debug("Sending data to LogScale...")
    headers = {
        "Authorization": f"Bearer {logscale_api_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(logscale_api_url, json=data, headers=headers)
    logging.debug(f"Response from LogScale: Status Code: {response.status_code}, Response: {response.text}")
    return response.status_code, response.text

# Main function
def main():
    try:
        logging.debug("Starting script...")
        config = load_config()
        logging.debug(f"Config loaded: {config}")
        latitude = float(config['latitude'])
        longitude = float(config['longitude'])
        alias = config['alias']
        encounter_id = config['encounter_id']

        # Get timezone
        timezone = get_timezone(latitude, longitude)
        logging.debug(f"Timezone found: {timezone}")

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
        logging.debug(f"Sun and moon information: {sun_and_moon_info}")

        # Fetch weather data
        weather_data = fetch_weather_data(latitude, longitude, config['date_start'], config['date_end'])

        # Generate log lines
        log_lines = generate_log_lines(weather_data, sun_and_moon_info, encounter_id, alias, config)

        # Send log lines to LogScale
        structured_data = [{"tags": {"host": "weatherhost", "source": "weatherdata"}, "events": [{"timestamp": event['@timestamp'], "attributes": event} for event in log_lines]}]
        status_code, response_text = send_to_logscale(LOGSCALE_URL, config['logscale_api_token_case_study'], structured_data)
        logging.debug(f"Status Code: {status_code}, Response: {response_text}")
    except Exception as e:
        logging.error(e)

if __name__ == "__main__":
    main()
