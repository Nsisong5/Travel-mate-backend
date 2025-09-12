import httpx 
from core.config import settings 
from fastapi import HTTPException 

async def get_location_id(dest: str):
    result = {}
    url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"
    headers = {
      "x-rapidapi-key": settings.FLIGHT_API_KEY,
 	"x-rapidapi-host": "booking-com15.p.rapidapi.com"
    
    }
    
    querystring = {
        "query": dest
    }
    async with httpx.AsyncClient() as client:
         try:
            response = await client.get(url, headers=headers,params=querystring)
            data = response.json()["data"]
            for x in range(len(data) -1):
                 destination = data[x]
                 if destination["city_name"].lower() == dest.lower():
                    result = destination
            return result
         except Exception as e:
            raise HTTPException(status_code =400, detail=str(e))