# Weather Ingestion Wizard for Falcon LogScale 🌩️

Welcome to the **Weather Ingestion Wizard for Falcon LogScale** repository! This project is your comprehensive solution for weather data ingestion, processing, and analysis, specifically designed to integrate seamlessly with Falcon LogScale. Whether you're a student or a professional, these scripts will help you leverage weather data to its fullest potential.

## 📂 Contents

- **Scripts**:
  - `01_log200_ingest_structured.py`: Ingests structured weather data with randomized values and sends it to LogScale.
  - `02_log200_ingest_raw.py`: Handles raw weather data, transforming and sending it to LogScale.
  - `03_log200_logcollector.py`: Collects logs systematically for weather data analysis.
  - `04_log200_case_study.py`: Retrieves historical weather data, enriches it with sun and moon information, and ingests it into LogScale.
  - `05_log200_periodic_fetch.py`: Performs hourly weather data fetches, detects extreme conditions, and allows users to input simulated data to trigger detections in LogScale.
- **Data**:
  - `atmospheric_monitoring.csv`: Sample CSV file with atmospheric monitoring data.
- **Configuration**:
  - `config.json`: Customize the weather data ingestion parameters here.
- **Utility**:
  - `menu.py`: The main interface for managing all scripts.

## 🚀 Getting Started

### Prerequisites

- Python 3.9
- Required libraries (detailed in `requirements.txt`):
  - `requests`
  - `astral`
  - `timezonefinder`
  - `pandas`
  - `numpy`
  - `meteostat`

### Installation

These scripts were developed and tested on an Amazon EC2 Linux host. Follow the steps below to set up your environment. While they are designed for Amazon EC2 Linux, they should also work on other Linux distributions that support Python 3.9 and the required libraries.

1. **Install Python 3.9**:
   - On Amazon Linux 2:
     ```bash
     sudo yum update
     sudo yum install python39
     python3.9 -m ensurepip --upgrade
     ```
   - On Ubuntu:
     ```bash
     sudo apt update
     sudo apt install python3.9 python3.9-venv python3.9-dev
     ```
   - On CentOS/RHEL:
     ```bash
     sudo yum update
     sudo yum install python39
     python3.9 -m ensurepip --upgrade
     ```
   - On Fedora:
     ```bash
     sudo dnf update
     sudo dnf install python3.9
     ```

2. **Clone the repository**:
    ```bash
    git clone https://github.com/cyberjack256/weather.git
    ```
3. **Navigate to the project directory**:
    ```bash
    cd weather
    ```
4. **Install the required libraries**:
    ```bash
    pip3.9 install -r requirements.txt
    ```

### Usage

Run the scripts through the intuitive menu interface. Execute the `menu.py` script to explore the various functionalities. This user-friendly menu will guide you through all the options without needing to remember individual script names.

    ```bash
    python3.9 menu.py
    ```

### Configuration

Tailor your experience by editing the `config.json` file. Here, you can add new data sources, adjust parameters, and configure the scripts to meet your specific needs.

## 🎓 About this Project

The **Weather Ingestion Wizard for Falcon LogScale** is crafted to support data ingestion and analysis learning in CrowdStrike's Falcon LogScale environment. This project provides a unique, hands-on learning experience by enabling the ingestion of diverse weather datasets for each student. It helps students generate and get data into LogScale quickly, using an open-source real-world dataset to test their connection and knowledge of ingestion APIs.

### LOG 200: Managing and Administering LogScale

These scripts are engineered to accelerate your proficiency with LogScale. As part of the LOG 200 course, they are designed to help users quickly and effectively manage and administer LogScale. Whether you're a student or a seasoned professional, these tools will enhance your capabilities with LogScale.

## 📜 Description

- `01_log200_ingest_structured.py`: Generates structured weather events with randomized data and ingests them into LogScale.
- `02_log200_ingest_raw.py`: Generates and ingests raw weather data logs into LogScale.
- `03_log200_logcollector.py`: Collects and organizes logs for comprehensive weather data analysis.
- `04_log200_case_study.py`: Fetches historical weather data, enriches it with additional information, and sends it to LogScale.
- `05_log200_periodic_fetch.py`: Performs hourly weather data fetches, detects extreme conditions, and allows users to input simulated weather data to trigger detections.

## 🤝 Contributing

We welcome your contributions to enhance these scripts. Fork the repository, implement your changes, and submit a pull request. Let's make these tools even more powerful together!

## 📜 License

This project is licensed under the Apache-2.0 License. See the [LICENSE](LICENSE) file for details.

## 📬 Contact

If you have questions or need support, please open an issue on this repository. We're here to help and will get back to you as soon as possible.

---

Happy weather data wrangling! ☀️🌧️❄️