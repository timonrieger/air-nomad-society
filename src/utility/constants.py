import json
import dotenv
import os

dotenv.load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY") 
DB_URI = os.getenv("DB_URI") 

with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'static', 'data.json'), 'r') as f:
    local_data = json.load(f)

TEQUILA_ENDPOINT = "https://api.tequila.kiwi.com"
TEQUILA_API_KEY = os.getenv("TEQUILA_API_KEY")
SMTP_EMAIL=os.getenv("SMTP_EMAIL")
SMTP_PWD=os.getenv("SMTP_PWD")
SMTP_SERVER=os.getenv("SMTP_SERVER")
SMTP_PORT=int(os.getenv("SMTP_PORT"))

JSON_DATA = local_data
DEPARTURE_CHOICES = [f"{city['city']} | {city['code']}" for city in JSON_DATA['cities']]
CURRENCY_CHOICES = JSON_DATA["currencies"]
COUNTRY_CHOICES = [country["country"] for country in JSON_DATA["countries"]]
ENVIRONMENT=os.getenv("ENVIRONMENT")
MY_UUID=os.getenv("MY_UUID")
