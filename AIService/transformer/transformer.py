import datetime
from enum import Enum 

# Define placeholder Enums as they appear in your sample data
# These would typically be imported from your application's models
class TripStatus(Enum):
    planned = 'planned'

class BudgetRange(Enum):
    medium = 'medium'
    low = 'low'
    high = 'high'

# --- Configuration for Mapping ---
# This dictionary defines how to map and default fields for the target 'past_trips' array items.
# Key: Target Field Name
# Value: A dictionary with 'source' (optional) and 'default' (optional)
FIELD_MAPPING = {
    "destination": {"source_fields": ['destination', 'country'], "handler": "get_full_destination"},
    "type": {"source": 'style', "default": 'general'}, 
    "duration": {"source_fields": ['start_date', 'end_date'], "handler": "calculate_duration"},
    "budget": {"source": 'budget_range', "handler": "map_budget_range"},
    "rating": {"source": 'rating', "default": 0.0, "type_cast": float},
    # Missing fields are handled with defaults
    "activities": {"default": ["general sightseeing", "relaxation"]} 
}

# --- Helper Functions for Complex Logic ---

def get_full_destination(trip: dict) -> str:
    """Concatenates destination and country."""
    destination_city = trip.get('destination', '').strip()
    country = trip.get('country', '').strip()
    
    if country and destination_city:
        return f"{destination_city}, {country}"
    return destination_city or country

def calculate_duration(trip: dict) -> int:
    """Calculates trip duration in days."""
    start_date = trip.get('start_date')
    end_date = trip.get('end_date')
    
    try:
        duration_days = (end_date - start_date).days
        # Treat same-day trips (duration 0) as 1 day
        return max(duration_days, 1)
    except (TypeError, AttributeError):
        return 1 # Default to 1 day if dates are invalid or missing

def map_budget_range(trip: dict) -> int:
    """Maps the BudgetRange Enum to a score (as seen in your target format)."""
    budget_enum = trip.get('budget_range')
    
    if budget_enum == BudgetRange.medium:
        return 60
    elif budget_enum == BudgetRange.high:
        return 80
    elif budget_enum == BudgetRange.low:
        return 40
    return 50 # Default score

# --- Default Preferences (Still static as they don't derive from trip data) ---

def _get_default_preferences() -> dict:
    """Provides a default set of user preferences."""
    return {
        "lifestyle": "budget",
        "travel_style": "mixed",
        "group_type": "couple", 
        "activities": "local culture, food, nature",
        "interests": "discovery, value, relaxation"
    }

# --- Main Dynamic Transformation Function ---

def transform_trip_data_dynamic(past_trips_data: list) -> dict:
    """
    Transforms a list of past trip data dictionaries into the required AI service 
    client format using a dynamic configuration.
    """
    if not past_trips_data:
        return {"user_id": None, "past_trips": [], "preferences": _get_default_preferences()}

    # Get user_id from the first trip
    user_id = past_trips_data[0].get('user_id')
    
    transformed_trips = []
    
    for trip in past_trips_data:
        transformed_trip = {}
        
        # Iterate over the configuration to build the target trip object
        for target_field, config in FIELD_MAPPING.items():
            value = None
            
            # 1. Use a custom handler function if defined
            if 'handler' in config:
                handler_func = globals().get(config['handler'])
                if handler_func:
                    value = handler_func(trip)
            
            # 2. Use a direct source field if defined and not already handled
            elif 'source' in config:
                value = trip.get(config['source'])

            # 3. Use the default value if the value is still None or the source was missing
            if value is None:
                value = config.get('default')
            
            # 4. Apply type casting if specified
            if value is not None and 'type_cast' in config:
                try:
                    value = config['type_cast'](value)
                except (ValueError, TypeError):
                    # Fallback to default if casting fails (e.g., trying to cast 'None' to float)
                    value = config.get('default', None) 
            
            # Assign the final value
            if value is not None:
                transformed_trip[target_field] = value

        transformed_trips.append(transformed_trip)
        
    return {
        "user_id": user_id,
        "past_trips": transformed_trips,
        "preferences": _get_default_preferences()
    }

# --- Example Usage (Using the previous sample data) ---
import json

sample_data = [
    {'id': 1, 'user_id': 1, 'destination': 'New Orleans', 'start_date': datetime.date(2025, 9, 24), 'end_date': datetime.date(2025, 9, 25), 'style': 'leisure', 'duration': '1 day', 'cost': 0.0, 'origin': 'Uyo, Nigeria ', 'status': TripStatus.planned, 'budget_range': BudgetRange.medium, 'created_at': datetime.datetime(2025, 9, 23, 0, 40, 30), 'means': 'car', 'cost_estimated': True, 'rating': 4, 'state': '', 'local_gov': '', 'country': 'United States', 'has_budget': True, 'title': None, 'travelers': 2}, 
    {'id': 2, 'user_id': 1, 'destination': 'Gzgzvzb', 'start_date': datetime.date(2025, 9, 23), 'end_date': datetime.date(2025, 9, 23), 'style': 'adventure', 'duration': '0 day', 'cost': 100.0, 'origin': 'Lagos, Nigeria ', 'status': TripStatus.planned, 'budget_range': BudgetRange.low, 'created_at': datetime.datetime(2025, 9, 23, 15, 35, 57), 'means': 'car', 'cost_estimated': True, 'rating': 4.8, 'state': '', 'local_gov': '', 'country': 'United Kingdom', 'has_budget': True, 'title': None, 'travelers': 2},
    {'id': 3, 'user_id': 2, 'destination': 'Lagos', 'start_date': datetime.date(2024, 1, 1), 'end_date': datetime.date(2024, 1, 15), 'style': 'business', 'duration': '14 days', 'cost': 500.0, 'origin': 'Abuja, Nigeria ', 'status': TripStatus.planned, 'budget_range': BudgetRange.high, 'created_at': datetime.datetime(2023, 12, 1, 0, 0, 0), 'means': 'flight', 'cost_estimated': False, 'rating': 5, 'state': '', 'local_gov': '', 'country': 'Nigeria', 'has_budget': True, 'title': 'Biz Trip', 'travelers': 1}
]

# Run the transformation
transformed_data = transform_trip_data_dynamic(sample_data)

print(json.dumps(transformed_data, indent=4))
