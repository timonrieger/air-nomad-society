class FlightData:
    # This class is responsible for structuring the flight data.

    def __init__(self, price, departure_city, departure_iata_code, arrival_city, arrival_iata_code, arrival_country,
                 from_date, to_date, link, currency, distance, stop_overs=0, via_city="", ):
        self.price = price,
        self.departure_city = departure_city,
        self.departure_iata_code = departure_iata_code,
        self.arrival_city = arrival_city,
        self.arrival_iata_code = arrival_iata_code,
        self.from_date = from_date,
        self.to_date = to_date,
        self.stop_overs = stop_overs,
        self.via_city = via_city
        self.link = link
        self.currency = currency
        self.arrival_country = arrival_country
        self.distance = distance
