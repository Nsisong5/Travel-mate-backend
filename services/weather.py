import os
import httpx
from core.config import settings 


async def get_weather_data(city: str):
     api_key = settings.WEATHER_API_KEY
     url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
     
     async with httpx.AsyncClient() as client:         
        response = await client.get(url)
        if response.status_code != 200:
           raise Exception(f"Error fetching weather data: {response.json().get('message')}")
          
        data = response.json()
      
        forecast = []
        for item in data["list"][:5]:
            forecast.append({
            "date": item["dt_txt"],
            "temp": item["main"]["temp"],
            "description": item["weather"][0]["description"]
        })
        return {
           "city": data["city"]["name"],
           "country": data["city"]["country"],
          "forecast": forecast  
          }