from fastapi import FastAPI, Query, BackgroundTasks, APIRouter, Depends 
from datetime import datetime, timedelta
from typing import List
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Optional
from AIService.AIService import ai_service
from database import get_db
from deps import get_current_user
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import models
import asyncio
from AIService.recs_generate import create_ai_recommendation
from  AIService.user_past_trips import get_trips
from AIService.transformer.transformer import transform_trip_data_dynamic 

router = APIRouter(prefix="/control")
# In production, replace this with a DB or Redis
recommendations_store = {
    "data": None,
    "last_generated": None
}







async def generate_recommendations(user_id=None):
    recommendations = None    
    if user_id:
        with next(get_db()) as db:
            trips = transform_trip_data_dynamic(get_trips(user_id, db)) 
        recommendations = await ai_service.get_destination_recommendations(trips)           
        print(recommendations)
        with next(get_db()) as db:
            for recommendation in recommendations:
              
               create_ai_recommendation(user_id,recommendation,db)               
    return recommendations



def get_all_user_ids_sync() -> List[int]:
    with next(get_db()) as db:
       return [user_id for (user_id,) in db.query(models.User.id).all()]


async def generate_and_store(user_id=None):
    if user_id:
        user_ids_to_process = [user_id]
    else:
        print("Scheduled job triggered. Fetching all users...")
        
        # Use asyncio.to_thread.run_in_executor to execute the blocking DB call in a separate thread
        try:
            user_ids_to_process = await asyncio.to_thread(get_all_user_ids_sync)
        except Exception as e:
            print(f"Error fetching users in scheduled job: {e}")
            return # Stop execution if fetching users fails

    if not user_ids_to_process:
        print("No users found to generate recommendations for.")
        return

    print(f"Starting recommendation generation for {len(user_ids_to_process)} user(s).")
    
    for uid in user_ids_to_process:
       await generate_recommendations(uid)  
            
    recommendations_store["last_generated"] = datetime.utcnow()
    print(f"[{recommendations_store['last_generated']}] Recommendations regenerated for all users {len(user_ids_to_process)}.")
    


# ==== SCHEDULED AUTO REFRESH ====
scheduler = AsyncIOScheduler()

scheduler.add_job(generate_and_store, "interval", hours = 24)
scheduler.start()


# ==== API ENDPOINTS ====

@router.get("/recommendations/{user_id}")
def get_recommendations(
    user: models.User = Depends(get_current_user),  
    force: bool = Query(False, description="Force regenerate recommendations"),
    background_tasks: BackgroundTasks = None
):
    """
    Returns cached recommendations by default.
    - If expired or missing, regenerate immediately.
    - If ?force=true, regenerate immediately.
    - Uses background task for non-blocking refresh if heavy.
    """
    now = datetime.utcnow()
    expiry_window = timedelta(hours= 30 * 24)  # cache expiry time

    need_refresh = (
        force
        or recommendations_store["last_generated"] is None
        or now - recommendations_store["last_generated"] > expiry_window
    )

    if need_refresh:
        # Non-blocking regeneration in background
        if background_tasks:
            background_tasks.add_task(generate_and_store,user.id)
        else:
            generate_and_store(user.id)

    return {
        "recommendations": recommendations_store["data"],
        "last_generated": recommendations_store["last_generated"],
        "force_regeneration": force,
        "cache_expiry_hours": expiry_window.total_seconds() / 3600
    }




@router.get("/trigger-recommendations")
def trigger_recommendations(
   background_tasks: BackgroundTasks,
   user: models.User = Depends(get_current_user)):
    
   """
    Explicit endpoint to trigger regeneration.
    Useful for admin panels or user actions.
    """
   background_tasks.add_task(generate_and_store,user.id)
   return {"status": "Regeneration started"}
   
   
   
