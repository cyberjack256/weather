import json
import os
import random
from datetime import datetime, timedelta
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Set the base directory relative to the script location
base_dir = os.path.dirname(__file__)

# Load and validate the configuration
def load_config():
    config_path = os.path.join(base_dir, 'config.json')
    with open(config_path, 'r') as file:
        config = json.load(file)
    if any(value == "REPLACEME" for value in config.values()):
        raise ValueError("Please replace all 'REPLACEME' fields in the config file.")
    return config

# Generate a raw log entry
def generate_raw_log(encounter_id, alias, units):
    timestamp = (datetime.utcnow() - timedelta(minutes=random.randint(1, 5))).isoformat() + "Z"

    if units == "imperial":
        temperature = random.randint(14, 95)  # °F
        wind_speed = random.randint(0, 62)  # mph
    else:
        temperature = random.randint(-10, 35)  # °C
        wind_speed = random.randint(0, 100)  # km/h

    humidity = random.randint(20, 90)  # %
    precipitation = random.choice([0, 1, 2, 5, 10, 20])  # mm

    raw_log = f"[{timestamp}] Temp: {temperature}{units}, Humidity: {humidity}%, Precipitation: {precipitation}mm, Wind Speed: {wind_speed}{units}, Encounter ID: {encounter_id}, Alias: {alias}"
    return raw_log

# Send data to LogScale
def send_to_logscale(logscale_api_url, logscale_api_token, data):
    headers = {
        "Authorization": f"Bearer {logscale_api_token}",
        "Content-Type": "text/plain"
    }
    response = requests.post(logscale_api_url, data=data, headers=headers)
    logging.debug(f"Response from LogScale: Status Code: {response.status_code}, Response: {response.text}")
    return response.status_code, response.text

# Main function
def main():
    try:
        logging.debug("Starting script...")
        config = load_config()
        logging.debug(f"Config loaded: {config}")
        
        # Generate a raw log entry
        raw_log = generate_raw_log(
            config["encounter_id"],
            config["alias"],
            config["units"]
        )

        # Send log data to LogScale
        status_code, response_text = send_to_logscale(
            config['logscale_api_url'],
            config['logscale_api_token_raw'],
            raw_log
        )

        print(f"Status Code: {status_code}, Response: {response_text}")
        
        # Provide guidance to students
        print("\n### Important: Read the Output ###\n")
        print("Sample Log Entry Sent:")
        print(raw_log)
        print("\nLog Entry Structure:")
        print("The log entry includes fields such as 'timestamp', 'temperature', 'humidity', 'precipitation', 'wind speed', 'encounter ID', and 'alias'.")
        print("\nUsing the LogScale Raw Ingest API:")
        print("The LogScale Raw Ingest API is used to ingest unstructured data directly. This means that the data being sent is a raw string that will be parsed using the attached parser.")
        print("\nSearch Hint:")
        print("To search for your data in LogScale, use the following query in your sandbox view:")
        print(f'observer.id = "{config["encounter_id"]}" AND observer.alias = "{config["alias"]}"')
        print("Make sure to adjust the time range to include the time when the logs were sent (e.g., '1m', '7d', etc.).")
        
    except Exception as e:
        logging.error(e)

if __name__ == "__main__":
    main()
