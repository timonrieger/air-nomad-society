import sys
import os, requests

# # getting the name of the directory
# # where the this file is present.
# current = os.path.dirname(os.path.realpath(__file__))

# # Getting the parent directory name
# # where the current directory is present.
# parent = os.path.dirname(current)

# # adding the parent directory to
# # the sys.path.
# sys.path.append(parent)

from app import app, db, AirNomads
from app.constants import NPOINT

class DataManager:
    # This class is responsible for talking to the Google Sheet and the Database.

    def __init__(self):
        self.destination_data = {}
        self.user_data = {}
        self.image_data = {}

    def get_user_data(self):
        with app.app_context():
            user_data = AirNomads.query.all()
        self.user_data = [{"token": user.token, "id": user.id, "username": user.username, "email": user.email,
                           "departureCity": user.departure_city, "departureIata": user.departure_iata,
                           "currency": user.currency, "nightsFrom": user.min_nights, "nightsTo": user.max_nights,
                           "dreamPlaces": user.travel_countries.split(",")} for user in user_data]
        return self.user_data

    def get_destination_data(self):
        self.destination_data = requests.get(url=NPOINT).json()["countries"]
        return self.destination_data

    def get_images(self):
        self.image_data = requests.get(url=NPOINT).json()["images"]
        return self.image_data
