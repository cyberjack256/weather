import json
import os
import logging
import requests
from datetime import datetime, timedelta
import random

# Set up logging
logging.basicConfig(level=logging.DEBUG)

CONFIG_FILE = 'config.json'

REQUIRED_FIELDS = ['logscale_api_token_raw', 'encounter_id', 'alias']

LOGSCALE_URL = 'https://cloud.us.humio.com/api/v1/ingest/humio-unstructured'

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

# Generate a raw log line
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

    raw_log = f"[{timestamp}] Temp: {temperature}°C, Humidity: {humidity}%, Precipitation: {precipitation}mm, Wind Speed: {wind_speed}km/h, Encounter ID: {encounter_id}, Alias: {alias}"
    return raw_log

# Send raw log data to LogScale
def send_to_logscale(raw_log, logscale_api_token):
    headers = {
        "Authorization": f"Bearer {logscale_api_token}",
        "Content-Type": "text/plain"
    }
    response = requests.post(LOGSCALE_URL, data=raw_log, headers=headers)
    return response.status_code, response.text

# Main function
def main():
    if not validate_config():
        return

    config = load_config()
    logscale_api_token = config['logscale_api_token_raw']
    encounter_id = config['encounter_id']
    alias = config['alias']
    units = config.get('units', 'metric')

    raw_log = generate_raw_log(encounter_id, alias, units)
    
    # Display the raw log line for user reference
    print("\nRaw log line that will be sent:")
    print(raw_log)

    print("\nDescription:")
    print("This script generates a raw log line with weather data attributes.")
    print("It then sends the log line to LogScale using the unstructured ingest API.")
    print("You can search for your data in LogScale using the following query:")
    print(f"observer.id={encounter_id} AND observer.alias={alias}")
    print("\nMake sure to set the time range for the logs appropriately in your LogScale view.")

    status_code, response_text = send_to_logscale(raw_log, logscale_api_token)
    logging.debug(f"Response from LogScale: Status Code: {status_code}, Response: {response_text}")

if __name__ == "__main__":
    main()
