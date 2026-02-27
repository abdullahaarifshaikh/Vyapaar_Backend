from pymongo import MongoClient
from config.settings import MONGO_URI, MONGO_DB_NAME

# Initialize MongoDB Client
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# Expose Collections
products_collection = db["products"]
customers_collection = db["customers"]
orders_collection = db["orders"]

# Create indexes for faster searches
products_collection.create_index("name", unique=True)
customers_collection.create_index("phone", unique=True)
