# points for AI Recommendations
from fastapi import HTTPException, Depends, Query, APIRouter,Header
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from deps import get_current_user
from database import get_db
import models
import schemas




def create_ai_recommendation(
    user_id: int,
    payload,   
    db: Session, 
):     
    """Create a new AI recommendation for the current user"""
    print(f"Payload received: {payload}")
 
    try:
        # Create recommendation object
        recommendation = models.AIRecommendation(
            user_id=user_id,
            category=payload["category"],
            location=payload["location"],
            name=payload["name"],
            destination_type=payload["destination_type"],
            title=payload["title"],
            description=payload["description"],
            image=payload["image"],
            image2=payload["image2"],
            image3=payload["image3"],
            image4=payload["image4"],
            tags=payload["tags"],
            popularity=payload["popularity"],
            rating=payload["rating"],
            budget_score=payload["budget_score"],
            budget_category = payload["budget_category"] or "Medium",
            lifestyle_category = payload["lifestyle_category"],
            settlement_type = payload["settlement_type"]
        )
        
        print(f"AI recommendation object created successfully")
        
        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)
        
        print(f"AI recommendation saved successfully with ID: {recommendation.id}")
        return recommendation
        
    except Exception as e:
        print(f"Error creating AI recommendation: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=422, detail=f"Failed to create recommendation: {str(e)}")
        
  