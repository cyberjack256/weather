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
    'city_name', 'country_name', 'latitude', 'longitude', 'units', 'extreme_field', 'extreme_level'
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

    # Convert units if necessary
    if units == "imperial":
        data["temp"] = data["temp"] * 9/5 + 32 if 'temp' in data else None
        data["dwpt"] = data["dwpt"] * 9/5 + 32 if 'dwpt' in data else None
        data["wspd"] = data["wspd"] * 2.23694 if 'wspd' in data else None
        data["wpgt"] = data["wpgt"] * 2.23694 if 'wpgt' in data else None
        data["prcp"] = data["prcp"] / 25.4 if 'prcp' in data else None
        data["snow"] = data["snow"] / 25.4 if 'snow' in data else None
        data["pres"] = data["pres"] * 0.02953 if 'pres' in data else None

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
                    "temperature": row.get("temp"),
                    "dew_point": row.get("dwpt"),
                    "relative_humidity": row.get("rhum"),
                    "precipitation": row.get("prcp"),
                    "snow": row.get("snow"),
                    "wind": {
                        "speed": row.get("wspd"),
                        "direction": row.get("wdir"),
                        "gust": row.get("wpgt")
                    },
                    "pressure": row.get("pres"),
                    "sunshine": row.get("tsun"),
                    "station_name": row.get("station_name", "N/A"),
                    "condition_code": row.get("coco"),
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

def generate_extreme_weather_data(weather_data, extreme_field, extreme_level, units):
    if extreme_field is None or extreme_field.lower() == 'none' or extreme_level is None or extreme_level.lower() == 'none':
        return weather_data, ""

    logging.debug(f"Generating extreme weather data for {extreme_field}...")
    extreme_values_metric = {
        "temp": (50, -50),  # High and low extreme temperatures in °C
        "wspd": (100, 0),    # High and low extreme wind speeds in km/h
        "prcp": (500, 0), # High and low extreme precipitation in mm
        "dwpt": (30, -30)     # High and low extreme dew points in °C
    }
    extreme_values_imperial = {
        "temp": (122, -58),  # High and low extreme temperatures in °F
        "wspd": (62.14, 0),   # High and low extreme wind speeds in mph
        "prcp": (19.69, 0),# High and low extreme precipitation in inches
        "dwpt": (86, -22)      # High and low extreme dew points in °F
    }

    extreme_values = extreme_values_imperial if units == 'imperial' else extreme_values_metric
    high_value, low_value = extreme_values.get(extreme_field, (None, None))
    if high_value is None or low_value is None:
        logging.error(f"Invalid extreme field: {extreme_field}")
        return weather_data, ""
    extreme_value = high_value if extreme_level.lower() == 'high' else low_value
    for time in weather_data.index:
        weather_data.at[time, extreme_field] = extreme_value
        # Set the appropriate weather condition code based on extreme values
        if extreme_field == "temp":
            weather_data.at[time, "coco"] = 1 if extreme_level.lower() == 'high' else 2  # Example condition codes
        elif extreme_field == "wspd":
            weather_data.at[time, "coco"] = 3 if extreme_level.lower() == 'high' else 4
        elif extreme_field == "prcp":
            weather_data.at[time, "coco"] = 5 if extreme_level.lower() == 'high' else 6
        elif extreme_field == "dwpt":
            weather_data.at[time, "coco"] = 7 if extreme_level.lower() == 'high' else 8
    alert_message = f"Extreme {extreme_field} alert: {extreme_value}"
    weather_data["alert"] = alert_message
    logging.debug(f"Extreme weather data: {weather_data}")
    return weather_data, alert_message

def get_moon_phase_name(moon_phase_value):
    if moon_phase_value < 0.125:
        return "New Moon"
    elif moon_phase_value < 0.25:
        return "Waxing Crescent"
    elif moon_phase_value < 0.375:
        return "First Quarter"
    elif moon_phase_value < 0.5:
        return "Waxing Gibbous"
    elif moon_phase_value < 0.625:
        return "Full Moon"
    elif moon_phase_value < 0.75:
        return "Waning Gibbous"
    elif moon_phase_value < 0.875:
        return "Last Quarter"
    else:
        return "Waning Crescent"

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
    extreme_field = config.get('extreme_field', 'none')
    extreme_level = config.get('extreme_level', 'none')

    # Get timezone
    timezone = get_timezone(latitude, longitude)

    # Fetch sun and moon data
    city = LocationInfo(config['city_name'], config['country_name'], timezone, latitude, longitude)
    date_specified = datetime.utcnow()
    s = sun(city.observer, date=date_specified, tzinfo=city.timezone)
    moon_phase_value = (phase(date_specified) % 30) / 30  # Normalize to [0, 1] range
    moon_phase_name = get_moon_phase_name(moon_phase_value)
    sun_and_moon_info = {
        'sun_info': {
            'dawn': s['dawn'].isoformat(),
            'sunrise': s['sunrise'].isoformat(),
            'noon': s['noon'].isoformat(),
            'sunset': s['sunset'].isoformat(),
            'dusk': s['dusk'].isoformat(),
        },
        'moon_phase': moon_phase_name
    }

    # Fetch weather data
    weather_data = fetch_weather_data(latitude, longitude, units)
    if weather_data.empty:
        logging.error("No weather data fetched.")
        return

    # Generate extreme weather data if specified
    alert_message = ""
    if extreme_field and extreme_field.lower() != 'none':
        weather_data, alert_message = generate_extreme_weather_data(weather_data, extreme_field, extreme_level, units)

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
