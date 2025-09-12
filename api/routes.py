from fastapi import APIRouter, HTTPException
from services.weather import get_weather_data
from services.currency import convert_currency
from services.flights import get_mock_flights,get_flights
from services.checklist import get_checklist
from services.hotels import get_hotels
from services.location_id import get_location_id

router = APIRouter()

@router.get("/weather")
async def get_weather(city :str ): 
      try:
          data = await get_weather_data(city)
          return data
      except Exception as e:
           raise HTTPException(status_code, detail=str(e))
           



@router.get("/currency")
async def currency(from_currency: str,to_currency : str, amount: float=1.0):
      try: 
         result = await convert_currency(from_currency,to_currency, amount)
         print(f"result: {result}")
         return result
      except Exception as e:
            raise HTTPException(status_code=500, detail=str("some error occurred"))
            
            
 
                                                                        
@router.get("/flights")
async def get_flights_data(airport_icao,date):
       try:
            flight  = await get_flights(airport_icao, date)         
            return flight 
       except Exception as e:
              raise HTTPException(status_code=400, detail=str(e))




@router.get("/checklist")
async def get_checklist_data(city : str):
     checklist = []
     try: 
        weather = await get_weather(city)             
        checklist = get_checklist(city, weather )
     except Exception as e:
          raise HTTPException(status_code=400, detail=str(e))
     if checklist:
        return checklist 
     raise HTTPException(status_code=500, detail="couldn't get checklist!")
      

     

@router.get("/destination")
async def get_destination_id(dest: str):
       id = None
       try:
            id = await get_location_id(dest)
            return id
       except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))



@router.get('/hotels')
async def get_hotels_list(dest):
     dest_data = {}
     try:
        dest_data = await get_destination_id(dest)
     except Exception as e:
          raise HTTPException(status_code=400, detail=str(f"Error when fetching destination data {e} "))
      
     try:
         print(dest_data)
         hotels = await get_hotels(dest_data)
         return hotels 
     except Exception as e:
          raise HTTPException(status_code=500, detail=f"Error during fetching hotels: {e}")











                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                