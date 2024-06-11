import requests
from meteostat import Point, Daily
from datetime import datetime

# Create a session with SSL verification disabled
session = requests.Session()
session.verify = False

# Set the location and date range
location = Point(42.3601, -71.0589)
start = datetime(2023, 1, 1)
end = datetime(2023, 1, 10)

# Fetch the weather data
data = Daily(location, start, end, model=True, session=session)

# Print the fetched data
print(data.fetch())
