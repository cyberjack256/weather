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
    if not config.get("logscale_api_token_raw"):
        config["logscale_api_token_raw"] = validate_input("Enter LogScale API Token (Raw)", "e.g., 7f51ecfe-71a5-4268-81d7-7f0c81c6105e", lambda x: bool(x))

    save_config(config)

    alias = config["alias"]
    encounter_id = config["encounter_id"]
    api_token = config["logscale_api_token_raw"]

    # Your existing script logic here
    logscale_api_url = "https://cloud.us.humio.com/api/v1/ingest/raw"

    # Example raw data to send
    raw_data = f"My raw Message generated at \"{datetime.utcnow().isoformat()}\""

    # Send data to LogScale
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(logscale_api_url, data=raw_data, headers=headers)
    logging.debug(f"Response from LogScale: Status Code: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    main()
