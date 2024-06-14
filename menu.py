import os
import json
import subprocess

LOGSCALE_API_URL = "https://cloud.us.humio.com/api/v1/ingest/humio-structured"

# Define configuration fields for each script
config_fields = {
    "01_log200_ingest_structured.py": ["alias", "encounter_id", "logscale_api_token_structured"],
    "02_log200_ingest_raw.py": ["alias", "encounter_id", "logscale_api_token_raw"],
    "04_log200_case_study.py": ["alias", "encounter_id", "logscale_api_token_case_study", "city_name", "country_name", "latitude", "longitude", "date_start", "date_end", "units"],
    "05_log200_periodic_fetch.py": ["alias", "encounter_id", "logscale_api_token_case_study", "city_name", "country_name", "latitude", "longitude", "extreme_field", "high"]
}

# Clear screen function
def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

# Load configuration
def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)

# Save configuration
def save_config(config):
    with open('config.json', 'w') as file:
        json.dump(config, file, indent=4)

# Show options
def show_options(script_name, required_fields):
    config = load_config()
    print(f"\nCurrent configuration for {script_name}:")
    for field in required_fields:
        print(f"{field}: {config.get(field, 'REPLACEME')}")
    input("\nPress Enter to continue...")

# Set option
def set_option(field):
    config = load_config()
    current_value = config.get(field, 'REPLACEME')
    clear_screen()
    print(f"Current value for {field}: {current_value}")
    new_value = input(f"Enter new value for {field}: ")
    if new_value:
        config[field] = new_value
        save_config(config)
        print(f"{field} updated successfully.")
    else:
        print(f"{field} not updated.")
    input("\nPress Enter to continue...")

# Validate and prompt for input
def prompt_for_input(prompt, current_value):
    clear_screen()
    print(f"Current value: {current_value}")
    value = input(f"Enter new value for {prompt}: ")
    return value if value else current_value

# Prompt for required fields
def prompt_for_required_fields(required_fields):
    config = load_config()
    for field in required_fields:
        config[field] = prompt_for_input(field, config.get(field, 'REPLACEME'))
    save_config(config)

# Run script and print response
def run_script(script_name):
    prompt_for_required_fields(config_fields[script_name])
    result = subprocess.run(['python3', script_name], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    input("\nPress Enter to continue...")

# Check and set cron job
def check_and_set_cron(script_name):
    cron_job = f"0 * * * * /usr/bin/python3 /home/ec2-user/weather/{script_name}"
    result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    if cron_job in result.stdout:
        overwrite = input("Cron job is already set. Do you want to overwrite it? (yes/no): ")
        if overwrite.lower() != 'yes':
            return
    subprocess.run(f'(crontab -l; echo "{cron_job}") | crontab -', shell=True)
    print("Cron job set successfully.")
    input("\nPress Enter to continue...")

# Run periodic fetch with extreme values
def run_periodic_fetch():
    config = load_config()
    config_fields_required = ["alias", "encounter_id", "logscale_api_token_case_study", "city_name", "country_name", "latitude", "longitude", "extreme_field", "high"]
    prompt_for_required_fields(config_fields_required)

    # Check if running as cron job
    run_as_cron = input("Do you want to set this script to run every hour as a cron job? (yes/no): ")
    if run_as_cron.lower() == 'yes':
        check_and_set_cron("05_log200_periodic_fetch.py")
        # Reset extreme fields after setting cron job
        config["extreme_field"] = "null"
        config["high"] = "null"
        save_config(config)
        return

    # Run once with extreme values
    result = subprocess.run(['python3', '05_log200_periodic_fetch.py'], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)

    # Reset extreme fields after running
    config["extreme_field"] = "null"
    config["high"] = "null"
    save_config(config)
    input("\nPress Enter to continue...")

# Menu options
def main_menu():
    while True:
        clear_screen()
        print("Weather Data Ingestion Menu\n")
        print("1. Show options for 01_log200_ingest_structured.py")
        print("2. Show options for 02_log200_ingest_raw.py")
        print("3. Show options for 04_log200_case_study.py")
        print("4. Show options for 05_log200_periodic_fetch.py")
        print("5. Set individual option")
        print("6. Run 01_log200_ingest_structured.py")
        print("7. Run 02_log200_ingest_raw.py")
        print("8. Run 04_log200_case_study.py")
        print("9. Run 05_log200_periodic_fetch.py")
        print("10. Exit")
        choice = input("\nEnter your choice: ")

        if choice == "1":
            show_options("01_log200_ingest_structured.py", config_fields["01_log200_ingest_structured.py"])
        elif choice == "2":
            show_options("02_log200_ingest_raw.py", config_fields["02_log200_ingest_raw.py"])
        elif choice == "3":
            show_options("04_log200_case_study.py", config_fields["04_log200_case_study.py"])
        elif choice == "4":
            show_options("05_log200_periodic_fetch.py", config_fields["05_log200_periodic_fetch.py"])
        elif choice == "5":
            clear_screen()
            print("Available fields to set:")
            all_fields = config_fields["01_log200_ingest_structured.py"] + \
                         config_fields["02_log200_ingest_raw.py"] + \
                         config_fields["04_log200_case_study.py"] + \
                         config_fields["05_log200_periodic_fetch.py"]
            unique_fields = list(set(all_fields))
            unique_fields.sort()  # Sort fields alphabetically for easier navigation
            for idx, field in enumerate(unique_fields, 1):
                print(f"{idx}. {field}")
            field_idx = input("\nEnter the number of the field to set: ")
            if field_idx.isdigit() and 1 <= int(field_idx) <= len(unique_fields):
                set_option(unique_fields[int(field_idx) - 1])
            else:
                print("Invalid field number.")
                input("\nPress Enter to continue...")
        elif choice == "6":
            run_script("01_log200_ingest_structured.py")
        elif choice == "7":
            run_script("02_log200_ingest_raw.py")
        elif choice == "8":
            run_script("04_log200_case_study.py")
        elif choice == "9":
            run_periodic_fetch()
        elif choice == "10":
            break
        else:
            input("Invalid choice. Press Enter to continue...")

if __name__ == "__main__":
    main_menu()
