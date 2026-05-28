import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWM_API_KEY = os.getenv("OWM_API_KEY", "")
TELEGRAM_PROXY = os.getenv("TELEGRAM_PROXY", "")

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "weather_bot.db"

OWM_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
OWM_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
OWM_GEOCODE_URL = "https://api.openweathermap.org/geo/1.0/direct"
OWM_REVERSE_GEOCODE_URL = "https://api.openweathermap.org/geo/1.0/reverse"
