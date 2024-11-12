import sys
import os

# # getting the name of the directory
# # where the this file is present.
# current = os.path.dirname(os.path.realpath(__file__))

# # Getting the parent directory name
# # where the current directory is present.
# parent = os.path.dirname(current)

# # adding the parent directory to
# # the sys.path.
# sys.path.append(parent)

from datetime import datetime
import requests, time
from flight_data import FlightData
from utility.constants import TEQUILA_API_KEY, TEQUILA_ENDPOINT

class FlightSearch:
    # This class is responsible for talking to the Flight Search API.

    def __init__(self):
        self.flight_search = {}

    def check_flight(self, departure_iata_code, arrival_iata_code, from_time, to_time, min_nights, max_nights, currency):
        search_endpoint = f"{TEQUILA_ENDPOINT}/search"
        headers = {"apikey": TEQUILA_API_KEY}
        query = {
            "fly_from": departure_iata_code,
            "fly_to": arrival_iata_code,
            "date_from": from_time.strftime("%d/%m/%Y"),
            "date_to": to_time.strftime("%d/%m/%Y"),
            "nights_in_dst_from": min_nights,
            "nights_in_dst_to": max_nights,
            "one_for_city": 1,
            "max_sector_stopovers": 0,
            "curr": currency
        }
        repeat = True
        repeat_round = 0
        while repeat:
            response = requests.get(url=search_endpoint, params=query, headers=headers)

            try:
                data = response.json()["data"][0]
            except IndexError:
                try:
                    query["max_sector_stopovers"] = 1
                    response = requests.get(url=search_endpoint, params=query, headers=headers)
                    data = response.json()["data"][0]
                except IndexError:
                    repeat = False
                    return None
                except KeyError:
                    repeat_round += 1
                    if repeat_round == 2:
                        repeat = False
                        return None
                    else:
                        time.sleep(10)
                        continue

                else:
                    flight_data = FlightData(
                        price=data["price"],
                        departure_city=data["cityFrom"],
                        departure_iata_code=data["flyFrom"],
                        arrival_city=data["cityTo"],
                        arrival_iata_code=data["flyTo"],
                        arrival_country=data["countryTo"]["name"],
                        from_date=datetime.fromtimestamp(data["route"][0]["dTime"]).strftime("%d.%m.%Y"),
                        to_date=datetime.fromtimestamp(data["route"][2]["aTime"]).strftime("%d.%m.%Y"),
                        stop_overs=1,
                        via_city=data["route"][0]["cityTo"],
                        link=data["deep_link"],
                        currency=currency,
                        distance=data["distance"]
                    )
                    repeat = False
                    return flight_data
            except KeyError:
                repeat_round += 1
                if repeat_round == 2:
                    repeat = False
                    return None
                else:
                    time.sleep(10)
                    continue
            else:
                flight_data = FlightData(
                    price=data["price"],
                    departure_city=data["cityFrom"],
                    departure_iata_code=data["flyFrom"],
                    arrival_city=data["cityTo"],
                    arrival_iata_code=data["flyTo"],
                    arrival_country=data["countryTo"]["name"],
                    from_date=datetime.fromtimestamp(data["route"][0]["dTime"]).strftime("%d.%m.%Y"),
                    to_date=datetime.fromtimestamp(data["route"][1]["aTime"]).strftime("%d.%m.%Y"),
                    via_city=False,
                    link=data["deep_link"],
                    currency=currency,
                    distance=data["distance"]
                )
                repeat = False
                return flight_data

    def get_destination_codes(self, city_name, country_name):
        location_endpoint = f"{TEQUILA_ENDPOINT}/locations/query"
        headers = {"apikey": TEQUILA_API_KEY}
        query = {"term": city_name, "location_types": "city"}
        response = requests.get(url=location_endpoint, params=query, headers=headers)
        matched_country = False
        location_nr = 0
        while not matched_country:
            try:
                if response.json()["locations"][location_nr]["country"]["name"] == country_name:
                    matched_country = True
                    code = response.json()["locations"][location_nr]["code"]
                else:
                    location_nr += 1
            except IndexError:
                code = response.json()["locations"][0]["code"]
                matched_country = True

        return code

############### test flight search api ################
# location_endpoint = f"{TEQUILA_ENDPOINT}/locations/query"
# headers = {"apikey": TEQUILA_API_KEY}
# query = {"term": "Tokelau", "location_types": "country"}
# code = requests.get(url=location_endpoint, params=query, headers=headers)
# matched_country = False
# location_nr = 0
# while not matched_country:
#    try:
#        if code.json()["locations"][location_nr]["country"]["name"] == "Germany":
#            matched_country = True
#            print(code.json()["locations"][location_nr]["code"])
#        else:
#            location_nr += 1
#    except IndexError or KeyError:
#        try:
#            print(code.json()["locations"][0]["code"])
#            matched_country = True
#        except IndexError:
#            print("The arrival city you provided has no airport or is not existing.")
#            matched_country = True
# print(code.text)
