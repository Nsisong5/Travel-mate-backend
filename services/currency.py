import httpx
from core.config import settings 

async def convert_currency(from_currency: str,to_currency: str, amount: float=1.0):
     
     url =     url = f"https://v6.exchangerate-api.com/v6/{settings.CURRENCY_API_KEY}/pair/{from_currency}/{to_currency}/{amount}" #f"https://api.exchangerate.host/convert?from={from_currency}&to={to_currency}&amount={amount}"
     async with httpx.AsyncClient() as client:
          response = await client.get(url)
          if response.status_code != 200:
            
               raise Exception('Error fetching currency data')
          data = response.json()
          return{
             "status": data["result"],
             "base_code": data["base_code"],
             "target_code": data["target_code"],
             "conversion_result": data["conversion_result"],
             
                     
          }
          