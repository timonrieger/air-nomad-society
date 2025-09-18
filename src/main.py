from datetime import datetime, timedelta
import random
from data_manager import DataManager
from flight_search import FlightSearch
from notification_manager import NotificationManager

data_manager = DataManager()
flight_search = FlightSearch()
notification_manager = NotificationManager()

data_manager.get_user_data()
data_manager.get_destination_data()
data_manager.get_images()

for user in data_manager.user_data:
    # Filter out excluded countries from gems selection
    available_destinations = [dest for dest in data_manager.destination_data 
                             if dest['country'] not in user["excludedCountries"]]
    
    selected_gems = random.sample(available_destinations, min(5, len(available_destinations)))
    added_new_item = False
    for index, item in enumerate(selected_gems):
        while item['country'] in user["dreamPlaces"]:
            new_item = random.choice(available_destinations)
            if new_item['country'] not in [item['country'] for item in selected_gems]:
                selected_gems[index] = new_item
                added_new_item = True
                break  # Exit the inner while loop
        if added_new_item:
            break  # Exit the outer for loop if a new item was added
    dream_places = []
    gem_places = []

    for destination in data_manager.destination_data:
        # reloading_requests += 1
        if destination["country"] == "" or destination["code"] == "":
            pass  # in case there is an empty line, skip this destination

        if destination["country"] in user["dreamPlaces"]:
            flight = flight_search.check_flight(
                departure_iata_code=user["departureIata"],
                arrival_iata_code=destination["code"],
                from_time=datetime.now() + timedelta(days=user["minDaysAhead"]),
                to_time=datetime.now() + timedelta(days=user["maxDaysAhead"]),
                min_nights=user["nightsFrom"],
                max_nights=user["nightsTo"],
                currency=user["currency"].upper()
            )
            if flight is None:
                continue

            elif flight.departure_city[0] != flight.arrival_city[0]:
                dream_places.append(
                    {
                        "price": int(float(flight.price[0])),
                        "currency": flight.currency,
                        "dep_city": flight.departure_city[0],
                        "dep_code": flight.departure_iata_code[0],
                        "arr_city": flight.arrival_city[0],
                        "arr_code": flight.arrival_iata_code[0],
                        "arr_country": flight.arrival_country,
                        "from_dt": flight.from_date[0],
                        "to_dt": flight.to_date[0],
                        "link": flight.link,
                        "stop_over": flight.via_city
                    }
                )

    for destination in selected_gems:
        flight = flight_search.check_flight(
            departure_iata_code=user["departureIata"],
            arrival_iata_code=destination["code"],
            from_time=datetime.now() + timedelta(days=user["minDaysAhead"]),
            to_time=datetime.now() + timedelta(days=user["maxDaysAhead"]),
            min_nights=user["nightsFrom"],
            max_nights=user["nightsTo"],
            currency=user["currency"].upper()
        )
        if flight is None:
            continue

        elif flight.departure_city[0] != flight.arrival_city[0]:
            gem_places.append(
                {
                    "price": int(float(flight.price[0])),
                    "currency": flight.currency,
                    "dep_city": flight.departure_city[0],
                    "dep_code": flight.departure_iata_code[0],
                    "arr_city": flight.arrival_city[0],
                    "arr_code": flight.arrival_iata_code[0],
                    "arr_country": flight.arrival_country,
                    "from_dt": flight.from_date[0],
                    "to_dt": flight.to_date[0],
                    "link": flight.link,
                    "stop_over": flight.via_city
                }
            )

    notification_manager.send_weekly_email(user=user, dream_flights=dream_places, random_flights=gem_places, image_data=data_manager.image_data)