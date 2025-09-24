from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")
    FLIGHT_API_KEY = os.getenv("FLIGHT_API_KEY")
    TM_PG_ADDRESS = os.getenv("TM_PG_ADRRES")
    SECRET_KEY =  os.getenv("SECRET_KEY")
    ALGORITHM =  os.getenv("ALGORITHM")
    # AI APIs
    GROQ_API_KEY = config("GROQ_API_KEY")
    HUGGINGFACE_API_KEY = config("HUGGINGFACE_API_KEY")
    
    # Image APIs
    UNSPLASH_ACCESS_KEY = config("UNSPLASH_ACCESS_KEY")
    PEXELS_API_KEY = config("PEXELS_API_KEY")
    
    # Free APIs (no keys needed)
    NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
    REST_COUNTRIES_BASE_URL = "https://restcountries.com/v3.1"
    

settings = Settings()
