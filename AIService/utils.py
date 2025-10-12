
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter 
import schemas 
import models
import json 
def format_travel_tips_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:

    
    # Initialize the dictionary to hold the formatted data
    formatted_data = {}

    # --- Culture Section ---
    culture = raw_data.get('culture', {})
    formatted_data['culture_customs'] = culture.get('customs', [])
    formatted_data['culture_etiquette'] = culture.get('etiquette', [])
    formatted_data['culture_dress_code'] = culture.get('dress_code', '')

    # --- Language Section ---
    language = raw_data.get('language', {})
    phrases = language.get('basic_phrases', {})
    # Aggregate basic phrases into a single list of key: value strings      
    formatted_data['language_basic_phrases'] = [f"{k}: {v}" for k, v in phrases.items()]
    formatted_data['language_tips'] = language.get('language_tips', '')

    # --- Practical Section ---
    practical = raw_data.get('practical', {})
    formatted_data['practical_currency'] = practical.get('currency', '')
    formatted_data['practical_tipping'] = practical.get('tipping', '')
    formatted_data['practical_transportation'] = practical.get('transportation', '')
    formatted_data['practical_safety'] = practical.get('safety', [])

    
    return formatted_data
    
    
def save_travel_tips_to_db(db,trip_id: int, raw_tips_data: Dict[str, Any]):
    formatted_data_dict = format_travel_tips_data(raw_tips_data)

    # 2. Pydantic Validation (Optional but good practice to ensure final structure)
    try:
        # Validate the formatted data against the FormattedTravelTips schema
        schemas.FormattedTravelTips(**formatted_data_dict)
    except Exception as e:
        # Raise an exception if the formatted data doesn't match the schema
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formatted data failed Pydantic validation: {e}"
        )

    # 3. Check for existing Trip and one-to-one constraint
    trip_exists = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip with ID {trip_id} not found."
        )

    # Check if tips already exist for this trip (enforcing unique trip_id on tips table)
    existing_tips = db.query(models.TravelTips).filter(models.TravelTips.trip_id == trip_id).first()
    if existing_tips:
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Travel tips for Trip ID {trip_id} already exist. Use PUT to update."
        )
        
    # 4. Database Insertion
    # Convert the formatted data dictionary back to a JSON string for storage
    tips_json_string = json.dumps(formatted_data_dict)
    
    db_tips = models.TravelTips(
        trip_id=trip_id,
        formatted_tips_json=tips_json_string
    )

    db.add(db_tips)
    db.commit()
    db.refresh(db_tips)
    
    return db_tips


        