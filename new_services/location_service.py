
import httpx
import asyncio
from typing import Dict, Optional
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class LocationService:
    def __init__(self):
        self.nominatim_base_url = settings.NOMINATIM_BASE_URL
        self.rest_countries_base_url = settings.REST_COUNTRIES_BASE_URL
        self.timeout = 10
        self.cache = {}  # Simple cache for location data
        self.cache_ttl = 86400  # 24 hours for location data
    
    async def get_location_info(self, location: str) -> Dict:
        """
        Get comprehensive location information
        
        Args:
            location: Location string (e.g., "Paris, France")
            
        Returns:
            Dictionary with coordinates, country info, currency, etc.
        """
        
        if not location.strip():
            return {"error": "Empty location"}
        
        # Check cache first
        cache_key = f"location_{location.lower().strip()}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Get fresh data
        geo_data = await self._get_geocoding_data(location)
        if not geo_data:
            result = {"error": "Location not found"}
            self._save_to_cache(cache_key, result)
            return result
        
        # Get country information
        country_code = geo_data.get("country_code", "").upper()
        country_info = await self._get_country_info(country_code)
        
        result = {
            "coordinates": {
                "lat": float(geo_data.get("lat", 0)),
                "lng": float(geo_data.get("lon", 0))
            },
            "display_name": geo_data.get("display_name", ""),
            "country": country_info.get("name", {}).get("common", ""),
            "country_code": country_code,
            "currency": self._extract_currency_info(country_info.get("currencies", {})),
            "languages": list(country_info.get("languages", {}).values()),
            "timezone": country_info.get("timezones", []),
            "region": self._extract_region(geo_data.get("display_name", "")),
            "continent": country_info.get("continents", []),
            "capital": country_info.get("capital", [])
        }
        
        # Cache the result
        self._save_to_cache(cache_key, result)
        logger.info(f"Retrieved location info for: {location}")
        
        return result
    
    async def _get_geocoding_data(self, location: str) -> Dict:
        """Get coordinates and basic info from Nominatim (OpenStreetMap)"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.nominatim_base_url}/search",
                    params={
                        "q": location,
                        "format": "json",
                        "limit": 1,
                        "addressdetails": 1,
                        "extratags": 1
                    },
                    headers={"User-Agent": "TravelMate-App/1.0 (contact@travelmate.com)"},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        return data[0]
                else:
                    logger.warning(f"Nominatim API error: {response.status_code}")
                    
        except asyncio.TimeoutError:
            logger.warning("Nominatim API timeout")
        except Exception as e:
            logger.warning(f"Nominatim API error: {e}")
        
        return {}
    
    async def _get_country_info(self, country_code: str) -> Dict:
        """Get country info from REST Countries API"""
        
        if not country_code:
            return {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.rest_countries_base_url}/alpha/{country_code}",
                    params={"fields": "name,currencies,languages,timezones,continents,capital"},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"REST Countries API error: {response.status_code}")
                    
        except asyncio.TimeoutError:
            logger.warning("REST Countries API timeout")
        except Exception as e:
            logger.warning(f"REST Countries API error: {e}")
        
        return {}
    
    def _extract_currency_info(self, currencies: Dict) -> Dict:
        """Extract useful currency information"""
        
        if not currencies:
            return {}
        
        # Get first currency (most countries have one primary currency)
        currency_code = next(iter(currencies.keys())) if currencies else ""
        currency_data = currencies.get(currency_code, {})
        
        return {
            "code": currency_code,
            "name": currency_data.get("name", ""),
            "symbol": currency_data.get("symbol", "")
        }
    
    def _extract_region(self, display_name: str) -> str:
        """Extract region from display name"""
        
        if not display_name:
            return ""
        
        parts = display_name.split(",")
        # Usually the region is the second-to-last part
        return parts[-2].strip() if len(parts) > 2 else ""
    
    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Get item from cache if not expired"""
        
        if key in self.cache:
            data, timestamp = self.cache[key]
            if (asyncio.get_event_loop().time() - timestamp) < self.cache_ttl:
                return data
            else:
                del self.cache[key]
        return None
    
    def _save_to_cache(self, key: str, data: Dict) -> None:
        """Save item to cache with timestamp"""
        
        self.cache[key] = (data, asyncio.get_event_loop().time())
        
        # Simple cache cleanup
        if len(self.cache) > 200:
            # Remove oldest 50 items
            sorted_items = sorted(self.cache.items(), key=lambda x: x[1][1])
            for old_key, _ in sorted_items[:50]:
                del self.cache[old_key]

# config.py - Update your config file
from decouple import config

class Settings:
    # AI APIs
    GROQ_API_KEY = config("GROQ_API_KEY", default="")
    HUGGINGFACE_API_KEY = config("HUGGINGFACE_API_KEY", default="")
    
    # Image APIs
    UNSPLASH_ACCESS_KEY = config("UNSPLASH_ACCESS_KEY", default="")
    PEXELS_API_KEY = config("PEXELS_API_KEY", default="")
    
    # Location APIs (Free - no keys needed)
    NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
    REST_COUNTRIES_BASE_URL = "https://restcountries.com/v3.1"
    
    # Database
    DATABASE_URL = config("DATABASE_URL")
    
    # Other settings
    SECRET_KEY = config("SECRET_KEY")
    CORS_ORIGINS = config("CORS_ORIGINS", default="http://localhost:3000").split(",")

settings = Settings()

# main.py - Add to your existing FastAPI app
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.travel_recommendations import router as travel_router

app = FastAPI(
    title="TravelMate API",
    description="AI-powered travel recommendations API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(travel_router)

@app.get("/")
async def root():
    return {"message": "TravelMate API is running", "version": "1.0.0"}

# test_integration.py - Complete test script
