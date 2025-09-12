from datetime import datetime 


today = datetime.now().date()



def get_checklist(city :str, weather, purpose : str = "business", travel_date: str = today):
     
     weather_condition = weather["forecast"][0]["description"]
     temperature = weather["forecast"][0]["temp"]
    
     destination = {
         "country": weather["country"],
         "city": weather["city"],
     }
     checklist = ["Passport", "Tickets", "Phone Charger"]

     if weather_condition.lower() in  ["rain", "drizzle", "thunderstorm", "light rain"] :
            checklist.append("Umbrella or Raincoat")
     if temperature < 15:
            checklist.append("Warm clothes")
     elif temperature > 30:
            checklist.append("Sunscreen and Sunglasses")

     if purpose == "business":
            checklist += ["Laptop", "Formal Wear"]
     else:
            checklist += ["Casual clothes", "Camera", "Snacks"]

     return {
            "destination": destination,
            "travel_date": travel_date,
            "weather_forecast": weather_condition,
            "temperature": temperature,
            "checklist": checklist
        }

     
     