import httpx
from datetime import datetime, timedelta
from core.config import settings 
from fastapi import HTTPException 

def get_mock_flights(from_airport: str, to_airport: str, date: str):
    try:
        # Validate date
        flight_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")

    flights = []
    for i in range(5):  # Generate 5 mock flights
        dep_time = (flight_date + timedelta(hours=6 + i * 2)).strftime("%Y-%m-%d %H:%M")
        arr_time = (flight_date + timedelta(hours=9 + i * 2)).strftime("%Y-%m-%d %H:%M")
        flights.append({
            "flight_number": f"{from_airport[:2].upper()}{to_airport[:2].upper()}-{100 + i}",
            "from": from_airport.upper(),
            "to": to_airport.upper(),
            "departure": dep_time,
            "arrival": arr_time,
            "airline": "SmartAir",
            "price_usd": round(300 + i * 45, 2)
        })

    return {
        "date": date,
        "from": from_airport.upper(),
        "to": to_airport.upper(),
        "flights": flights
    }
    




API_HOST = "aerodatabox.p.rapidapi.com"


async def get_flights(
    airport_icao: str ,
    date: str
):


    dt = datetime.strptime(date, "%Y-%m-%d")
    from_time = int(dt.timestamp())
    to_time = int(dt + timedelta(hours=12))
    url = f"https://{API_HOST}/flights/airports/icao/{airport_icao}/{from_time}/{to_time}"

    headers = {
        "X-RapidAPI-Key": settings.FLIGHT_API_KEY,
        "X-RapidAPI-Host": API_HOST
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"API error: {response.text}"
                )

            data = response.json()
            return {
                "airport": airport_icao,
                "date": date,
                "arrivals": data.get("arrivals", []),
                "departures": data.get("departures", [])
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")  
                                