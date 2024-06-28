import json
import os
import logging
import subprocess

# Set up logging
logging.basicConfig(level=logging.DEBUG)

CONFIG_FILE = 'config.json'
LOGSCALE_URL = 'https://cloud.us.humio.com/api/v1/ingest/humio-structured'

REQUIRED_FIELDS = {
    '01': ['logscale_api_token_structured', 'encounter_id', 'alias'],
    '02': ['logscale_api_token_raw', 'encounter_id', 'alias'],
    '04': ['logscale_api_token_case_study', 'city_name', 'country_name', 'latitude', 'longitude', 'date_start', 'date_end', 'encounter_id', 'alias'],
    '05': ['logscale_api_token_case_study', 'city_name', 'country_name', 'latitude', 'longitude', 'extreme_field', 'extreme_level', 'encounter_id', 'alias']
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
    'encounter_id': 'e.g., jt30-0000000000000',
    'alias': 'e.g., racing-jack',
    'units': '<metric> or imperial',
    'extreme_field': 'temperature, wind_speed, precipitation, dew_point, or <none>',
    'extreme_level': 'high, low, or <none>'
}

EXTREME_FIELDS = ['temperature', 'wind_speed', 'precipitation', 'dew_point', 'none']
EXTREME_LEVELS = ['high', 'low', 'none']

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
    
    if field == 'extreme_field':
        print("Select the extreme field:")
        for i, value in enumerate(EXTREME_FIELDS, 1):
            print(f"{i}. {value}")
        choice = input(f"Enter the number for the extreme field ({example}):\n").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(EXTREME_FIELDS):
            config[field] = EXTREME_FIELDS[int(choice) - 1]
        else:
            print("Invalid choice. Setting to default (none).")
            config[field] = 'none'
    elif field == 'extreme_level':
        print("Select the extreme level:")
        for i, value in enumerate(EXTREME_LEVELS, 1):
            print(f"{i}. {value}")
        choice = input(f"Enter the number for the extreme level ({example}):\n").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(EXTREME_LEVELS):
            config[field] = EXTREME_LEVELS[int(choice) - 1]
        else:
            print("Invalid choice. Setting to default (none).")
            config[field] = 'none'
    else:
        new_value = input(f"Enter the value for {field} ({example}):\n").strip()
        config[field] = new_value
    
    save_config(config)
    print(f"Configuration updated: {field} set to {config[field]}")

# Validate configuration
def validate_config(script_id):
    config = load_config()
    missing_fields = [field for field in REQUIRED_FIELDS[script_id] if field not in config or config[field] == '' or config[field] == 'REPLACEME']
    if missing_fields:
        print(f"\nMissing required fields for script {script_id}: {', '.join(missing_fields)}")
        return False
    return True

# Run script
def run_script(script_id, script_name):
    if not validate_config(script_id):
        print("\nPlease set the missing configuration fields using option 5.")
        return
    result = subprocess.run(['python3', script_name], capture_output=True, text=True)
    with open('script_output.txt', 'w') as f:
        f.write(result.stdout)
        f.write(result.stderr)
    subprocess.run(['less', 'script_output.txt'])

# Set up cron job
def setup_cron_job():
    cron_job = "0 * * * * /usr/bin/python3 /home/ec2-user/weather/05_log200_periodic_fetch.py\n"
    cron_exists = False

    try:
        existing_crontab = subprocess.check_output(['sudo', 'crontab', '-l', '-u', 'ec2-user']).decode()
        if cron_job in existing_crontab:
            cron_exists = True
    except subprocess.CalledProcessError:
        existing_crontab = ""

    if not cron_exists:
        with open('crontab_tmp', 'w') as f:
            f.write(existing_crontab)
            f.write(cron_job)
        subprocess.check_call(['sudo', 'crontab', 'crontab_tmp', '-u', 'ec2-user'])
        os.remove('crontab_tmp')
        print("Cron job set to run every hour.")
    else:
        print("Cron job is already set.")

# Show cron job
def show_cron_job():
    try:
        existing_crontab = subprocess.check_output(['sudo', 'crontab', '-l', '-u', 'ec2-user']).decode()
        print(f"Current crontab for ec2-user:\n{existing_crontab}")
    except subprocess.CalledProcessError:
        print("No crontab set for ec2-user.")

# Delete cron job
def delete_cron_job():
    try:
        existing_crontab = subprocess.check_output(['sudo', 'crontab', '-l', '-u', 'ec2-user']).decode()
        cron_job = "0 * * * * /usr/bin/python3 /home/ec2-user/weather/05_log200_periodic_fetch.py\n"
        if cron_job in existing_crontab:
            new_crontab = existing_crontab.replace(cron_job, "")
            with open('crontab_tmp', 'w') as f:
                f.write(new_crontab)
            subprocess.check_call(['sudo', 'crontab', 'crontab_tmp', '-u', 'ec2-user'])
            os.remove('crontab_tmp')
            print("Cron job deleted.")
        else:
            print("Cron job not found.")
    except subprocess.CalledProcessError:
        print("No crontab set for ec2-user.")

# Main menu
def main_menu():
    while True:
        os.system('clear')
        print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                              CrowdStrike Menu                              ║
║════════════════════════════════════════════════════════════════════════════║
║ Welcome to the CrowdStrike Weather Data Ingest Menu                        ║
║ Please select an option:                                                   ║
║                                                                            ║
║  1. Show options for 01_log200_ingest_structured.py (Structured Data)      ║
║  2. Show options for 02_log200_ingest_raw.py (Unstructured Data)           ║
║  3. Show options for 04_log200_case_study.py (Historical Data)             ║
║  4. Show options for 05_log200_periodic_fetch.py (Periodic Fetch)          ║
║  5. Set a configuration field                                              ║
║  6. Run 01_log200_ingest_structured.py                                     ║
║  7. Run 02_log200_ingest_raw.py                                            ║
║  8. Run 04_log200_case_study.py                                            ║
║  9. Run 05_log200_periodic_fetch.py                                        ║
║ 10. Set up cron job for 05_log200_periodic_fetch.py                        ║
║ 11. Show current cron job for 05_log200_periodic_fetch.py                  ║
║ 12. Delete cron job for 05_log200_periodic_fetch.py                        ║
║  0. Exit                                                                   ║
╚════════════════════════════════════════════════════════════════════════════╝
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
            sorted_fields = sorted(FIELD_EXAMPLES.keys())
            for i, field in enumerate(sorted_fields, 1):
                print(f"{i}. {field}")
            field_choice = input("\nEnter the number of the field you want to set: ").strip()
            if field_choice.isdigit() and 1 <= int(field_choice) <= len(sorted_fields):
                field = sorted_fields[int(field_choice) - 1]
                set_config_field(field)
            else:
                print("Invalid choice. Please enter a number from the list.")
        elif choice == '6':
            if validate_config('01'):
                run_script('01', '01_log200_ingest_structured.py')
            else:
                print("\nPlease set the missing configuration fields using option 5.")
        elif choice == '7':
            if validate_config('02'):
                run_script('02', '02_log200_ingest_raw.py')
            else:
                print("\nPlease set the missing configuration fields using option 5.")
        elif choice == '8':
            if validate_config('04'):
                run_script('04', '04_log200_case_study.py')
            else:
                print("\nPlease set the missing configuration fields using option 5.")
        elif choice == '9':
            if validate_config('05'):
                run_script('05', '05_log200_periodic_fetch.py')
            else:
                print("\nPlease set the missing configuration fields using option 5.")
        elif choice == '10':
            setup_cron_job()
        elif choice == '11':
            show_cron_job()
        elif choice == '12':
            delete_cron_job()
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main_menu()
