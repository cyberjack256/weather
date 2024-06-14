import json
import os
import logging
import subprocess
import random
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.DEBUG)

CONFIG_FILE = 'config.json'

LOGSCALE_URL = 'https://cloud.us.humio.com/api/v1/ingest/humio-structured'

REQUIRED_FIELDS = {
    '01': ['logscale_api_token_structured', 'encounter_id', 'alias'],
    '02': ['logscale_api_token_raw', 'encounter_id', 'alias'],
    '04': ['logscale_api_token_case_study', 'city_name', 'country_name', 'latitude', 'longitude', 'date_start', 'date_end', 'encounter_id', 'alias'],
    '05': ['logscale_api_token_case_study', 'city_name', 'country_name', 'latitude', 'longitude', 'extreme_field', 'high', 'encounter_id', 'alias']
}

# Field examples
FIELD_EXAMPLES = {
    'logscale_api_token_structured': 'e.g., 7f51ecfe-71a5-4268-81d7-7f0c81c6105d',
    'logscale_api_token_raw': 'e.g., 7f51ecfe-71a5-4268-81d7-7f0c81c6105e',
    'logscale_api_token_case_study': 'e.g., 7f51ecfe-71a5-4268-81d7-7f0c81c6105f',
    'city_name': 'e.g., Ann Arbor',
    'country_name': 'e.g., US',
    'latitude': 'e.g., 42.2808',
    'longitude': 'e.g., -83.7430',
    'date_start': 'e.g., 2023-04-01',
    'date_end': 'e.g., 2024-04-01',
    'encounter_id': 'e.g., jt30',
    'alias': 'e.g., racing-jack',
    'units': 'e.g., metric or imperial',
    'extreme_field': 'e.g., temperature',
    'high': 'e.g., true or false'
}

# Load configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    return {}

# Save configuration
def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)

# Show current configuration
def show_config(script_id):
    config = load_config()
    print(f"\nCurrent configuration for script {script_id}:")
    for field in REQUIRED_FIELDS[script_id]:
        value = config.get(field, 'Not set')
        print(f"{field}: {value}")

# Set configuration field
def set_config_field(field):
    config = load_config()
    example = FIELD_EXAMPLES.get(field, '')
    new_value = input(f"Enter the value for {field} ({example}): ").strip()
    config[field] = new_value
    save_config(config)
    print(f"Configuration updated: {field} set to {new_value}")

# Validate configuration
def validate_config(script_id):
    config = load_config()
    missing_fields = [field for field in REQUIRED_FIELDS[script_id] if field not in config or config[field] == '']
    if missing_fields:
        print(f"\nMissing required fields for script {script_id}: {', '.join(missing_fields)}")
        return False
    return True

# Run script
def run_script(script_id, script_name):
    if not validate_config(script_id):
        return
    subprocess.run(['python3', script_name])

# Main menu
def main_menu():
    while True:
        os.system('clear')
        print("""
Welcome to the Weather Data Ingest Menu
Please select an option:

1. Show options for script 01
2. Show options for script 02
3. Show options for script 04
4. Show options for script 05
5. Set a configuration field
6. Run script 01
7. Run script 02
8. Run script 04
9. Run script 05
0. Exit
        """)
        choice = input("Enter your choice: ").strip()

        if choice == '1':
            show_config('01')
        elif choice == '2':
            show_config('02')
        elif choice == '3':
            show_config('04')
        elif choice == '4':
            show_config('05')
        elif choice == '5':
            field = input(f"Enter the field name to set ({', '.join(FIELD_EXAMPLES.keys())}): ").strip()
            if field in FIELD_EXAMPLES:
                set_config_field(field)
            else:
                print("Invalid field name.")
        elif choice == '6':
            run_script('01', '01_log200_ingest_structured.py')
        elif choice == '7':
            run_script('02', '02_log200_ingest_raw.py')
        elif choice == '8':
            run_script('04', '04_log200_case_study.py')
        elif choice == '9':
            run_script('05', '05_log200_periodic_fetch.py')
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main_menu()
