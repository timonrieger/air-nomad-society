import requests
import dotenv
import os

dotenv.load_dotenv()

GMAIL = os.getenv("GMAIL")
GMAIL_PWD = os.getenv("GMAIL_PWD")
NPOINT = os.getenv("NPOINT")
ANS_GMAIL = os.getenv("ANS_GMAIL")
ANS_GMAIL_PWD = os.getenv("ANS_GMAIL_PWD")
TEQUILA_ENDPOINT = "https://api.tequila.kiwi.com"
TEQUILA_API_KEY = os.getenv("TEQUILA_API_KEY")

npoint_data = requests.get(url=NPOINT).json()

DEPARTURE_CHOICES = [f"{city['city']} | {city['code']}" for city in npoint_data['cities']]
CURRENCY_CHOICES = npoint_data["currencies"]
COUNTRY_CHOICES = [country["country"] for country in npoint_data["countries"]]
