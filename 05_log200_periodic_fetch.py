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
from meteostat import Point, Hourly, Stations
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

# Save configuration
def save_config(config):
    config_path = os.path.join(base_dir, CONFIG_FILE)
    with open(config_path, 'w') as file:
        json.dump(config, file, indent=4)

# Initialize TimezoneFinder
def get_timezone(latitude, longitude):
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=latitude, lng=longitude)
    if tz_name:
        return ZoneInfo(tz_name)
    else:
        raise Exception("Could not determine the timezone.")

# Fetch weather data for the current hour
def fetch_weather_data(latitude, longitude):
    logging.debug("Fetching weather data...")
    location = Point(latitude, longitude)
    now = datetime.utcnow()
    start = now - timedelta(hours=1)
    end = now
    data = Hourly(location, start, end)
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
def generate_log_lines(weather_data, sun_and_moon_info, encounter_id, alias, config, alert_message):
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
                "temperature": row["temp"],
                "dew_point": row["dwpt"],
                "relative_humidity": row["rhum"],
                "precipitation": row["prcp"],
                "snow": row["snow"],
                "wind": {
                    "speed": row["wspd"],
                    "direction": row["wdir"],
                    "gust": row["wpgt"]
                },
                "pressure": row["pres"],
                "sunshine": row["tsun"],
                "station_name": row.get("station_name", "N/A"),
                "alert": alert_message
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
        # Update the extreme field with the extreme value
        if alert_message:
            extreme_field = config.get('extreme_field')
            if extreme_field and extreme_field in log_entry['weather']:
                extreme_value = row[extreme_field]
                log_entry['weather'][extreme_field] = extreme_value
        log_lines.append(log_entry)
    logging.debug(f"Generated log lines: {log_lines}")
    return log_lines

# Modify weather data to create extreme weather conditions
def generate_extreme_weather_data(weather_data, extreme_field, high):
    logging.debug(f"Generating extreme weather data for {extreme_field}...")
    extreme_values = {
        "temperature": (50, -50),  # High and low extreme temperatures
        "wind_speed": (100, 0),    # High and low extreme wind speeds
        "precipitation": (500, 0), # High and low extreme precipitation
        "dew_point": (30, -30)     # High and low extreme dew points
    }
    high_value, low_value = extreme_values.get(extreme_field, (None, None))
    if high_value is None or low_value is None:
        logging.error(f"Invalid extreme field: {extreme_field}")
        return weather_data, ""
    extreme_value = high_value if high else low_value
    for time in weather_data.index:
        weather_data.at[time, extreme_field] = extreme_value
    alert_message = f"Extreme {extreme_field} alert: {extreme_value}"
    weather_data["alert"] = alert_message
    logging.debug(f"Extreme weather data: {weather_data}")
    return weather_data, alert_message

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
        extreme_field = config.get('extreme_field', None)
        high = config.get('high', True)

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
        weather_data = fetch_weather_data(latitude, longitude)

        # Generate extreme weather data if specified
        alert_message = ""
        if extreme_field:
            weather_data, alert_message = generate_extreme_weather_data(weather_data, extreme_field, high)

        # Generate log lines
        log_lines = generate_log_lines(weather_data, sun_and_moon_info, encounter_id, alias, config, alert_message)

        # Send log lines to LogScale
        structured_data = [{"tags": {"host": "weatherhost", "source": "weatherdata"}, "events": [{"timestamp": event['@timestamp'], "attributes": event} for event in log_lines]}]
        status_code, response_text = send_to_logscale(LOGSCALE_URL, config['logscale_api_token_case_study'], structured_data)
        logging.debug(f"Status Code: {status_code}, Response: {response_text}")
        
        # Reset extreme values to null for cron job
        config['extreme_field'] = None
        config['high'] = None
        save_config(config)
    except Exception as e:
        logging.error(e)

if __name__ == "__main__":
    main()
