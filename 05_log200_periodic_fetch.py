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
import pandas as pd
import numpy as np
from meteostat import Point, Hourly, Stations

# Set up logging
logging.basicConfig(level=logging.DEBUG)

CONFIG_FILE = 'config.json'
REQUIRED_FIELDS = [
    'logscale_api_token_case_study', 'encounter_id', 'alias',
    'city_name', 'country_name', 'latitude', 'longitude', 'units'
]
LOGSCALE_URL = 'https://cloud.us.humio.com/api/v1/ingest/humio-structured'

# Load configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    return {}

# Validate configuration
def validate_config():
    config = load_config()
    missing_fields = [field for field in REQUIRED_FIELDS if field not in config or config[field] == '']
    if missing_fields:
        print(f"\nMissing required fields: {', '.join(missing_fields)}")
        return False
    return True

def get_timezone(latitude, longitude):
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=latitude, lng=longitude)
    if tz_name:
        return ZoneInfo(tz_name)
    else:
        raise Exception("Could not determine the timezone.")

def fetch_weather_data(latitude, longitude, units):
    location = Point(latitude, longitude)
    now = datetime.utcnow()
    start = now - timedelta(hours=1)
    end = now
    data = Hourly(location, start, end)
    data = data.fetch()

    # Enrich data with nearest weather station information
    stations = Stations()
    stations = stations.nearby(latitude, longitude)
    station = stations.fetch(1)
    if not station.empty:
        station_name = station.name.iloc[0]
        data['station_name'] = station_name

    # Replace NaN and infinite values with None to avoid JSON serialization issues
    data = data.replace([np.nan, np.inf, -np.inf], None)
    return data

def generate_log_lines(weather_data, sun_and_moon_info, encounter_id, alias, config, alert_message):
    if weather_data.empty:
        logging.error("Weather data is empty.")
        return []

    log_lines = []
    for time, row in weather_data.iterrows():
        log_entry = {
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "attributes": {
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
        }
        log_lines.append(log_entry)
    return log_lines

def send_to_logscale(log_lines, logscale_api_token):
    headers = {
        "Authorization": f"Bearer {logscale_api_token}",
        "Content-Type": "application/json"
    }
    payload = [{
        "tags": {
            "host": "weatherhost",
            "source": "weatherdata"
        },
        "events": log_lines
    }]
    response = requests.post(LOGSCALE_URL, json=payload, headers=headers)
    return response.status_code, response.text

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

def main():
    if not validate_config():
        return

    config = load_config()
    logscale_api_token = config['logscale_api_token_case_study']
    encounter_id = config['encounter_id']
    alias = config['alias']
    latitude = float(config['latitude'])
    longitude = float(config['longitude'])
    units = config['units']
    extreme_field = config.get('extreme_field', None)
    high = config.get('high', True)

    # Get timezone
    timezone = get_timezone(latitude, longitude)

    # Fetch sun and moon data
    city = LocationInfo(config['city_name'], config['country_name'], timezone, latitude, longitude)
    date_specified = datetime.utcnow()
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

    # Fetch weather data
    weather_data = fetch_weather_data(latitude, longitude, units)
    if weather_data.empty:
        logging.error("No weather data fetched.")
        return

    # Generate extreme weather data if specified
    alert_message = ""
    if extreme_field and extreme_field.lower() != 'null':
        weather_data, alert_message = generate_extreme_weather_data(weather_data, extreme_field, high)

    # Generate log lines
    log_lines = generate_log_lines(weather_data, sun_and_moon_info, encounter_id, alias, config, alert_message)
    if not log_lines:
        logging.error("No log lines generated.")
        return

    # Display an example log line for user reference
    example_log_line = json.dumps(log_lines[0], indent=4)
    print("\nExample Log Line:")
    print(example_log_line)

    # Description of the log line structure
    print("\nDescription:")
    print("The log line includes various details such as:")
    print("- Timestamp (@timestamp)")
    print("- Geolocation (city_name, country_name, latitude, longitude)")
    print("- Observer information (alias, id)")
    print("- Weather details (temperature, humidity, wind speed, etc.)")
    print("- Sun and moon information (sunrise, sunset, moon phase)")
    print("\nThe structured data is ingested into LogScale using the humio-structured API endpoint.")

    # How to search for the data in LogScale
    print("\nHow to Search for Your Data in LogScale:")
    print(f"1. Go to your LogScale view and set the time range from {date_specified.strftime('%Y-%m-%d')} to {date_specified.strftime('%Y-%m-%d')}.")
    print(f"2. Use the following query to search for your data:")
    print(f"observer.id={encounter_id} AND observer.alias={alias}")

    status_code, response_text = send_to_logscale(log_lines, logscale_api_token)
    logging.debug(f"Response from LogScale: Status Code: {status_code}, Response: {response_text}")

if __name__ == "__main__":
    main()
