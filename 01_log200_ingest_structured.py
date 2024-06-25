import json
import os
import random
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

# Set up logging
import logging
logging.basicConfig(level=logging.DEBUG)

CONFIG_FILE = 'config.json'
REQUIRED_FIELDS = ['logscale_api_token_structured', 'encounter_id', 'alias']
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

def generate_weather_event(encounter_id: str, alias: str, units: str = "metric") -> Dict[str, Any]:
    """
    Generate a weather event with random data.
    Args:
        encounter_id (str): The encounter ID for the event.
        alias (str): The alias for the event.
        units (str): The units of measurement, either 'imperial' or 'metric'.
    Returns:
        Dict[str, Any]: The generated weather event data.
    """
    # Generate a timestamp for the event
    timestamp = (datetime.now() - timedelta(days=random.randint(1, 6))).isoformat() + 'Z'

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
            "observer.id": encounter_id,
            "observer.alias": alias
        }
    }
    return json_event

def construct_curl_command(logscale_api_url, logscale_api_token, data):
    """
    Construct a curl command for sending the structured data to LogScale.
    Args:
        logscale_api_url (str): The LogScale API URL.
        logscale_api_token (str): The LogScale API token.
        data (List[Dict[str, Any]]): The structured data to send.
    Returns:
        str: The constructed curl command.
    """
    curl_command = (
        f"curl {logscale_api_url} -X POST "
        f"-H 'Authorization: Bearer {logscale_api_token}' "
        f"-H 'Content-Type: application/json' "
        f"--data '{json.dumps(data)}'"
    )
    return curl_command

def send_to_logscale(logscale_api_token: str, data: List[Dict[str, Any]]) -> Tuple[int, str]:
    headers = {
        "Authorization": f"Bearer {logscale_api_token}",
        "Content-Type": "application/json"
    }
    structured_data = [{
        "tags": {
            "host": "weatherhost",
            "source": "weatherdata"
        },
        "events": data
    }]
    curl_command = construct_curl_command(LOGSCALE_URL, logscale_api_token, structured_data)
    
    print(f"\nSample Message:\n{json.dumps(data[0], indent=4)}")
    print(f"\nSample Curl Command:\n{curl_command}")
    print("\nBreakdown of Curl Command:")
    print("1. `curl`: Command line tool for transferring data with URLs.")
    print(f"2. `{LOGSCALE_URL}`: The URL to which the data is sent.")
    print("3. `-X POST`: Specifies the request method to be POST.")
    print("4. `-H 'Authorization: Bearer {logscale_api_token}'`: Adds the authorization header with the Bearer token for authentication.")
    print("5. `-H 'Content-Type: application/json'`: Specifies the content type of the data being sent as JSON.")
    print("6. `--data '{json.dumps(data)}'`: The actual structured data to be sent in the body of the POST request.")
    
    response = requests.post(LOGSCALE_URL, json=structured_data, headers=headers)
    return response.status_code, response.text

def main():
    if not validate_config():
        return

    config = load_config()
    logscale_api_token = config['logscale_api_token_structured']
    encounter_id = config['encounter_id']
    alias = config['alias']

    # Generate weather events
    weather_events = [generate_weather_event(encounter_id, alias) for _ in range(5)]

    # Display an example log line for user reference
    example_log_line = json.dumps(weather_events[0], indent=4)
    print("\nExample Log Line:")
    print(example_log_line)

    # Description of the log line structure
    print("\nDescription:")
    print("The log line includes various details such as:")
    print("- Timestamp (timestamp)")
    print("- Temperature (temperature)")
    print("- Humidity Percentage (humidity_percentage)")
    print("- Precipitation (precipitation)")
    print("- Wind Speed (wind_speed)")
    print("- Message (message)")
    print("- Observer ID (observer.id)")
    print("- Observer Alias (observer.alias)")
    print("\nThe structured data is ingested into LogScale using the humio-structured API endpoint.")

    # How to search for the data in LogScale
    print("\nHow to Search for Your Data in LogScale:")
    print(f"1. Go to your LogScale view and set the time range from the past week.")
    print(f"2. Use the following query to search for your data:")
    print(f"observer.id={encounter_id} AND observer.alias={alias}")

    # Send data to LogScale
    status_code, response_text = send_to_logscale(logscale_api_token, weather_events)
    logging.debug(f"Response from LogScale: Status Code: {status_code}, Response: {response_text}")

if __name__ == "__main__":
    main()