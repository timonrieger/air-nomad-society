import json
import dotenv
import os

dotenv.load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY") 
DB_URI = os.getenv("DB_URI") 

# Path to the local data.json file
DATA_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'static', 'data.json')

# Load data from local JSON file instead of NPOINT
with open(DATA_FILE_PATH, 'r') as f:
    local_data = json.load(f)

TEQUILA_ENDPOINT = "https://api.tequila.kiwi.com"
TEQUILA_API_KEY = os.getenv("TEQUILA_API_KEY")
SMTP_EMAIL=os.getenv("SMTP_EMAIL")
SMTP_PWD=os.getenv("SMTP_PWD")
SMTP_SERVER=os.getenv("SMTP_SERVER")
SMTP_PORT=int(os.getenv("SMTP_PORT"))

DEPARTURE_CHOICES = [f"{city['city']} | {city['code']}" for city in local_data['cities']]
CURRENCY_CHOICES = local_data["currencies"]
COUNTRY_CHOICES = [country["country"] for country in local_data["countries"]]
ENVIRONMENT=os.getenv("ENVIRONMENT")
MY_UUID=os.getenv("MY_UUID")
