import os
from dotenv import load_dotenv

load_dotenv()

# Google API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "karobaar_inventory")

# WhatsApp
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "YOUR_LONG_ACCESS_TOKEN_HERE")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "YOUR_PHONE_NUMBER_ID_HERE")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "1234")

# Sarvam AI
SARV_API = os.getenv("SARV_API")
