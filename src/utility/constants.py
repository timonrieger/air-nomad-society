import requests
import dotenv
import os

dotenv.load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY") 
DB_URI = os.getenv("DB_URI") 

NPOINT = os.getenv("NPOINT")
TEQUILA_ENDPOINT = "https://api.tequila.kiwi.com"
TEQUILA_API_KEY = os.getenv("TEQUILA_API_KEY")
SMTP_EMAIL=os.getenv("SMTP_EMAIL")
SMTP_PWD=os.getenv("SMTP_PWD")
SMTP_SERVER=os.getenv("SMTP_SERVER")
SMTP_PORT=int(os.getenv("SMTP_PORT"))

npoint_data = requests.get(url=NPOINT).json()

DEPARTURE_CHOICES = [f"{city['city']} | {city['code']}" for city in npoint_data['cities']]
CURRENCY_CHOICES = npoint_data["currencies"]
COUNTRY_CHOICES = [country["country"] for country in npoint_data["countries"]]
ENVIRONMENT=os.getenv("ENVIRONMENT")
MY_UUID=os.getenv("MY_UUID")
