import sys
import os, json

# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))

# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)

# adding the parent directory to
# the sys.path.
sys.path.append(parent)

from app import app, AirNomads
from utility.constants import ENVIRONMENT, MY_UUID, DATA_FILE_PATH

class DataManager:
    '''This class is responsible for loading data from local JSON file and the database.'''

    def __init__(self):
        self.destination_data = {}
        self.user_data = {}
        self.image_data = {}

    def get_user_data(self):
        with app.app_context():
            if ENVIRONMENT == "dev":
                user_data = [AirNomads.query.filter_by(id=MY_UUID).first()]
            else:
                user_data = AirNomads.query.all()
        self.user_data = [{"token": user.token, "id": user.id, "username": user.username, "email": user.email,
                           "departureCity": user.departure_city, "departureIata": user.departure_iata,
                           "currency": user.currency, "nightsFrom": user.min_nights, "nightsTo": user.max_nights,
                           "minDaysAhead": user.min_days_ahead, "maxDaysAhead": user.max_days_ahead,
                           "dreamPlaces": user.travel_countries.split(","),
                           "excludedCountries": user.excluded_countries.split(",") if user.excluded_countries else []} for user in user_data]
        return self.user_data

    def get_destination_data(self):
        # Load data from local JSON file instead of NPOINT
        with open(DATA_FILE_PATH, 'r') as f:
            data = json.load(f)
        self.destination_data = data["countries"]
        return self.destination_data

    def get_images(self):
        # Load data from local JSON file instead of NPOINT
        with open(DATA_FILE_PATH, 'r') as f:
            data = json.load(f)
        self.image_data = data["images"]
        return self.image_data
