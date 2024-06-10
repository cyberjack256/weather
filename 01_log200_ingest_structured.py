import random
import json
import requests
from datetime import datetime, timedelta
import logging
from typing import Dict, Tuple, Any, List

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def generate_weather_event(encounter_id: str, units: str) -> Dict[str, Any]:
    """
    Generate a weather event with random data.
    Args:
        encounter_id (str): The encounter ID for the event.
        units (str): The units of measurement, either 'imperial' or 'metric'.
    Returns:
        Dict[str, Any]: The generated weather event data.
    """
    # Generate a timestamp for the event
    timestamp = (datetime.now() - timedelta(days=random.randint(1, 6))).isoformat() + 'Z'
    
    if units == "imperial":
        # Generate weather-related event data in imperial units
        temperature = random.randint(14, 95)  # °F
        wind_speed = random.randint(0, 62)  # mph
    else:
        # Generate weather-related event data in metric units
        temperature = random.randint(-10, 35)  # °C
        wind_speed = random.randint(0, 100)  # km/h

    event_data = {
        "message": f"Weather update at timestamp {timestamp}",
        "temperature": temperature,
        "humidity_percentage": random.randint(20, 90),  # %
        "precipitation": f"{random.choice([0, 1, 2, 5, 10, 20])} mm",
        "wind_speed": wind_speed
    }

    # Create JSON event in the format expected by LogScale
    json_event = {
        "timestamp": timestamp,
        "attributes": {
            "temperature": event_data["temperature"],
            "humidity_percentage": event_data["humidity_percentage"],
            "precipitation": event_data["precipitation"],
            "wind_speed": event_data["wind_speed"],
            "message": event_data["message"],
            "source": "/home/ec2-user/var/log/weather.log",
            "sourcetype": "weatherdata",
            "env": "prod",
            "group.id": encounter_id
        }
    }

    return json_event

def send_to_logscale(logscale_api_url: str, logscale_api_token: str, data: List[Dict[str, Any]]) -> Tuple[int, str]:
    """
    Send data to LogScale.
    Args:
        logscale_api_url (str): The LogScale API URL.
        logscale_api_token (str): The LogScale API token.
        data (List[Dict[str, Any]]): The data to send.
    Returns:
        Tuple[int, str]: The HTTP status code and response text.
    """
    headers = {
        "Authorization": f"Bearer {logscale_api_token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(logscale_api_url, json=data, headers=headers)
        response.raise_for_status()
        return response.status_code, response.text
    except requests.RequestException as e:
        logging.error(f"Failed to send data to LogScale: {e}")
        raise

def load_config() -> Dict[str, str]:
    """
    Load and validate the configuration from the config.json file.
    Returns:
        Dict[str, str]: The loaded configuration.
    """
    config_path = 'config.json'
    try:
        with open(config_path, 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        logging.error("Configuration file not found.")
        raise
    except json.JSONDecodeError:
        logging.error("Error decoding JSON from the configuration file.")
        raise

    required_keys = ['logscale_api_url', 'logscale_api_token_structured', 'encounter_id']
    for key in required_keys:
        if key not in config or config[key] == "REPLACEME":
            raise ValueError(f"Please replace all 'REPLACEME' fields in the config file. Missing: {key}")

    return config

def main():
    """Main function to load configuration, generate events, and send them to LogScale."""
    try:
        config = load_config()
        logging.debug(f"Config loaded: {config}")

        logscale_api_url = config['logscale_api_url']
        logscale_api_token = config['logscale_api_token_structured']
        encounter_id = config['encounter_id']
        units = config.get('units', 'metric')

        events = [generate_weather_event(encounter_id, units) for _ in range(50)]

        # Structure the data payload for LogScale
        structured_data = [{
            "tags": {
                "host": "weatherhost",
                "source": "weatherdata"
            },
            "events": events
        }]

        status_code, response_text = send_to_logscale(logscale_api_url, logscale_api_token, structured_data)
        logging.debug(f"Status Code: {status_code}, Response: {response_text}")
        print(f"Status Code: {status_code}, Response: {response_text}")

    except Exception as e:
        logging.error("An error occurred: ", exc_info=True)
        print(e)

if __name__ == "__main__":
    main()
