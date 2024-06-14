import json
import os
import logging
import requests
from datetime import datetime

# Set up logging
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

# Generate a sample log line
def generate_sample_log(encounter_id, alias):
    timestamp = datetime.utcnow().isoformat() + "Z"
    log_line = {
        "tags": {
            "host": "server1",
            "source": "application.log"
        },
        "events": [
            {
                "timestamp": timestamp,
                "attributes": {
                    "encounter_id": encounter_id,
                    "alias": alias,
                    "temperature": 22.5,
                    "humidity": 60
                }
            }
        ]
    }
    return log_line

# Send log data to LogScale
def send_to_logscale(log_data, logscale_api_token):
    headers = {
        "Authorization": f"Bearer {logscale_api_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(LOGSCALE_URL, json=log_data, headers=headers)
    return response.status_code, response.text

# Main function
def main():
    if not validate_config():
        return

    config = load_config()
    logscale_api_token = config['logscale_api_token_structured']
    encounter_id = config['encounter_id']
    alias = config['alias']

    log_data = generate_sample_log(encounter_id, alias)
    
    # Display a sample log line for user reference
    print("\nSample log line that will be sent:")
    print(json.dumps(log_data, indent=4))

    print("\nDescription:")
    print("This script generates a structured log line with weather data attributes.")
    print("It then sends the log line to LogScale using the structured ingest API.")
    print("You can search for your data in LogScale using the following query:")
    print(f"observer.id={encounter_id} AND observer.alias={alias}")
    print("\nMake sure to set the time range for the logs appropriately in your LogScale view.")

    status_code, response_text = send_to_logscale(log_data, logscale_api_token)
    logging.debug(f"Response from LogScale: Status Code: {status_code}, Response: {response_text}")

if __name__ == "__main__":
    main()
