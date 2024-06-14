import os
import json

LOGSCALE_API_URL = "https://cloud.us.humio.com/api/v1/ingest/humio-structured"

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

# Menu options
def main_menu():
    config_fields = {
        "01_log200_ingest_structured.py": ["alias", "encounter_id", "logscale_api_token_structured"],
        "02_log200_ingest_raw.py": ["alias", "encounter_id", "logscale_api_token_raw"],
        "04_log200_case_study.py": ["alias", "encounter_id", "logscale_api_token_case_study", "city_name", "country_name", "latitude", "longitude", "date_start", "date_end", "units"],
        "05_log200_periodic_fetch.py": ["alias", "encounter_id", "logscale_api_token_case_study", "city_name", "country_name", "latitude", "longitude", "extreme_field", "high"]
    }

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
            for field in unique_fields:
                print(f" - {field}")
            field = input("\nEnter the field to set: ")
            if field in unique_fields:
                set_option(field)
            else:
                print("Invalid field name.")
                input("\nPress Enter to continue...")
        elif choice == "6":
            prompt_for_required_fields(config_fields["01_log200_ingest_structured.py"])
            os.system('python3 01_log200_ingest_structured.py')
        elif choice == "7":
            prompt_for_required_fields(config_fields["02_log200_ingest_raw.py"])
            os.system('python3 02_log200_ingest_raw.py')
        elif choice == "8":
            prompt_for_required_fields(config_fields["04_log200_case_study.py"])
            os.system('python3 04_log200_case_study.py')
        elif choice == "9":
            prompt_for_required_fields(config_fields["05_log200_periodic_fetch.py"])
            os.system('python3 05_log200_periodic_fetch.py')
        elif choice == "10":
            break
        else:
            input("Invalid choice. Press Enter to continue...")

if __name__ == "__main__":
    main_menu()
