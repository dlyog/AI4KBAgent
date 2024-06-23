import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    COSMOSDB_URI = os.getenv('COSMOSDB_URI')
    SERVICENOW_INSTANCE = os.getenv('SERVICENOW_INSTANCE')
    SERVICENOW_USER = os.getenv('SERVICENOW_USER')
    SERVICENOW_PASSWORD = os.getenv('SERVICENOW_PASSWORD')
