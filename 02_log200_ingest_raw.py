import json
import os
import random
import requests
from datetime import datetime, timedelta
from typing import Dict, Any

# Set up logging
import logging
logging.basicConfig(level=logging.DEBUG)

CONFIG_FILE = 'config.json'
REQUIRED_FIELDS = ['logscale_api_token_raw', 'encounter_id', 'alias']
LOGSCALE_URL = 'https://cloud.us.humio.com/api/v1/ingest/raw'

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

def generate_raw_log(encounter_id, alias, units):
    """
    Generate a raw log entry with random weather data.
    Args:
        encounter_id (str): The encounter ID for the event.
        alias (str): The alias for the event.
        units (str): The units of measurement, either 'imperial' or 'metric'.
    Returns:
        str: The generated raw log entry.
    """
    timestamp = (datetime.utcnow() - timedelta(minutes=random.randint(1, 5))).isoformat() + "Z"

    temperature = random.randint(-10, 35)  # °C
    wind_speed = random.randint(0, 100)  # km/h

    humidity = random.randint(20, 90)  # %
    precipitation = random.choice([0, 1, 2, 5, 10, 20])  # mm

    raw_log = f"[{timestamp}] Temp: {temperature}°C, Humidity: {humidity}%, Precipitation: {precipitation}mm, Wind Speed: {wind_speed}km/h, Encounter ID: {encounter_id}, Alias: {alias}"

    return raw_log

def construct_curl_command(logscale_api_url, logscale_api_token, raw_log):
    """
    Construct a curl command for sending the log to LogScale.
    Args:
        logscale_api_url (str): The LogScale API URL.
        logscale_api_token (str): The LogScale API token.
        raw_log (str): The raw log message.
    Returns:
        str: The constructed curl command.
    """
    curl_command = f"curl {logscale_api_url} -X POST -H 'Authorization: Bearer {logscale_api_token}' -H 'Content-Type: text/plain' --data '{raw_log}'"
    return curl_command

def send_to_logscale(logscale_api_url, logscale_api_token, raw_log):
    """
    Send raw log data to LogScale.
    Args:
        logscale_api_url (str): The LogScale API URL.
        logscale_api_token (str): The LogScale API token.
        raw_log (str): The raw log message.
    Returns:
        Tuple[int, str]: The HTTP status code and response text.
    """
    logging.info("Sending raw log data to LogScale...")
    headers = {
        "Authorization": f"Bearer {logscale_api_token}",
        "Content-Type": "text/plain"
    }
    curl_command = construct_curl_command(logscale_api_url, logscale_api_token, raw_log)
    explainshell_url = f"https://explainshell.com/explain?cmd={requests.utils.quote(curl_command)}"
    print(f"\nCurl Command:\n{curl_command}")
    print(f"\nExplainshell Link:\n{explainshell_url}\n")
    
    try:
        response = requests.post(logscale_api_url, data=raw_log, headers=headers)
        response.raise_for_status()
        logging.info(f"Response from LogScale: Status Code: {response.status_code}, Response: {response.text}")
        return response.status_code, response.text
    except requests.RequestException as e:
        logging.error(f"Failed to send raw log data to LogScale: {e}")
        raise

def main():
    """Main function to load configuration, generate raw logs, and send them to LogScale."""
    try:
        if not validate_config():
            return

        config = load_config()
        logscale_api_url = LOGSCALE_URL
        logscale_api_token = config['logscale_api_token_raw']
        encounter_id = config['encounter_id']
        alias = config['alias']
        units = config.get('units', 'metric')

        for _ in range(5):  # Generate 5 log entries
            raw_log = generate_raw_log(encounter_id, alias, units)
            logging.info(f"Generated raw log: {raw_log}")
            status_code, response_text = send_to_logscale(logscale_api_url, logscale_api_token, raw_log)
            logging.info(f"Status Code: {status_code}, Response: {response_text}")

        # Display an example log line for user reference
        example_log_line = generate_raw_log(encounter_id, alias, units)
        print("\nExample Log Line:")
        print(example_log_line)

        # Description of the log line structure
        print("\nDescription:")
        print("The log line includes various details such as:")
        print("- Timestamp (timestamp)")
        print("- Temperature (Temp)")
        print("- Humidity (Humidity)")
        print("- Precipitation (Precipitation)")
        print("- Wind Speed (Wind Speed)")
        print("- Encounter ID (Encounter ID)")
        print("- Alias (Alias)")
        print("\nThe raw data is ingested into LogScale using the raw API endpoint.")

        # How to search for the data in LogScale
        print("\nHow to Search for Your Data in LogScale:")
        print(f"1. Go to your LogScale view and set the time range from the past week.")
        print(f"2. Use the following query to search for your data:")
        print(f"observer.id={encounter_id} AND observer.alias={alias}")

    except Exception as e:
        logging.error("An error occurred: ", exc_info=True)
        print(e)

if __name__ == "__main__":
    main()