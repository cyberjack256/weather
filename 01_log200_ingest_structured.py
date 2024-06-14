import json
import os
from datetime import datetime
import requests
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

def main():
    config = load_config()

    # Check and prompt for required values if missing
    if not config.get("alias"):
        config["alias"] = validate_input("Enter alias", "e.g., racing-jack", lambda x: bool(x))
    if not config.get("encounter_id"):
        config["encounter_id"] = validate_input("Enter encounter ID", "e.g., jt30", lambda x: bool(x))
    if not config.get("logscale_api_token_structured"):
        config["logscale_api_token_structured"] = validate_input("Enter LogScale API Token (Structured)", "e.g., 7f51ecfe-71a5-4268-81d7-7f0c81c6105d", lambda x: bool(x))

    save_config(config)

    alias = config["alias"]
    encounter_id = config["encounter_id"]
    api_token = config["logscale_api_token_structured"]

    # Your existing script logic here
    logscale_api_url = config.get("logscale_api_url")
    if not logscale_api_url:
        logscale_api_url = validate_input("Enter LogScale API URL", "e.g., https://cloud.us.humio.com/api/v1/ingest/humio-structured", lambda x: bool(x))

    # Example data to send
    data = [
        {
            "tags": {"host": "weatherhost", "source": "weatherdata"},
            "events": [
                {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "attributes": {
                        "@timestamp": datetime.utcnow().isoformat() + "Z",
                        "geo": {"city_name": "Ann Arbor", "country_name": "US", "location": {"lat": "42.2808", "lon": "-83.7430"}},
                        "observer": {"alias": alias, "id": encounter_id},
                        "ecs": {"version": "1.12.0"},
                        "weather": {
                            "temperature": 20.0,
                            "dew_point": 10.0,
                            "relative_humidity": 80,
                            "precipitation": 5.0,
                            "snow": 0.0,
                            "wind": {"speed": 10.0, "direction": 180, "gust": 15.0},
                            "pressure": 1012.0,
                            "sunshine": 8.0,
                            "station_name": "Ann Arbor Station"
                        },
                        "event": {"created": datetime.utcnow().isoformat() + "Z", "module": "weather", "dataset": "weather"},
                        "sun": {"sunrise": "2024-06-11T06:00:00Z", "noon": "2024-06-11T12:00:00Z", "dusk": "2024-06-11T18:00:00Z", "sunset": "2024-06-11T18:30:00Z", "dawn": "2024-06-11T05:30:00Z"},
                        "moon_phase": 0.5
                    }
                }
            ]
        }
    ]

    # Send data to LogScale
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(logscale_api_url, json=data, headers=headers)
    logging.debug(f"Response from LogScale: Status Code: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    main()