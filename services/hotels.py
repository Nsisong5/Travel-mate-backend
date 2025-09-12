from core.config import settings 
from datetime import datetime, timedelta
import requests
import httpx

from fastapi import HTTPException 

today = datetime.now().date()
next_tommorrow = today + timedelta(days=2)


async def get_hotels(dest_data,budget_class: str = "business class"):
   headers = {
    "X-RapidAPI-Key": settings.FLIGHT_API_KEY,
    "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
    }

   url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"

   params = {   
      "search_type": "CITY",
      "units": "metric",
      "adults": 1,
      "room_number": 1,    
      "locale": "en-us",
      "arrival_date": today,
      "departure_date": next_tommorrow,
      "dest_id": dest_data['city_ufi'],
     
     }
   async with httpx.AsyncClient() as client:
            try: 
               response = await client.get(url,headers=headers, params=params)
               data = response.json()
               print(data)
               return data
            except Exception as e:
               raise HTTPException(status_code=400, detail=str(e))                     





#def get_dummy_hotels():

#  url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"

#  querystring = {
#  "dest_id":"-2003575",
#  "search_type":"CITY",
#  "arrival_date": today,
#  "departure_date": next_tommorrow,
#  "adults":"1",
#  "children_age":"0,17",
#  "room_qty":"1",
#  "page_number":"1",
#  "units":"metric",
#  "temperature_unit":"c",
#  "languagecode":"en-us",
#  "currency_code":"AED",
#  }

#  headers = {
#	"x-rapidapi-key": settings.FLIGHT_API_KEY,
#	"x-rapidapi-host": "booking-com15.p.rapidapi.com"
#   }

#  response = requests.get(url, headers=headers, params=querystring)

#  return response.json()                                                                                                                          