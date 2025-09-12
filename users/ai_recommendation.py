# FastAPI endpoints for AI Recommendations
from fastapi import HTTPException, Depends, Query, APIRouter,Header
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from deps import get_current_user
from database import get_db
import models
import schemas

router = APIRouter()




@router.post("/ai-recommendations", response_model=schemas.AIRecommendationOut)
def create_ai_recommendation(
    payload: schemas.AIRecommendationCreate, 
    db: Session = Depends(get_db), 
    user: models.User = Depends(get_current_user)

):     
    """Create a new AI recommendation for the current user"""
    print(f"Creating AI recommendation for user: {user.email}")
    print(f"Payload received: {payload.dict()}")
    
    try:
        # Create recommendation object
        recommendation = models.AIRecommendation(
            user_id=user.id,
            category=payload.category,
            location=payload.location,
            name=payload.name,
            destination_type=payload.destination_type,
            title=payload.title,
            description=payload.description,
            image=payload.image,
            image2=payload.image2,
            image3=payload.image3,
            image4=payload.image4,
            tags=payload.tags,
            popularity=payload.popularity,
            rating=payload.rating,
            budget_score=payload.budget_score,
            budget_category = payload.budget_category or "Medium",
            lifestyle_category = payload.lifestyle_category,
            settlement_type = payload.settlement_type
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
        
        
@router.get("/ai-recommendations", response_model=List[schemas.AIRecommendationOut])
def get_user_ai_recommendations(
    category: Optional[str] = Query(None, description="Filter by category"),
    location: Optional[str] = Query(None, description="Filter by location"),
    destination_type: Optional[str] = Query(None, description="Filter by type"),
    min_rating: Optional[float] = Query(None, description="Minimum rating filter"),
    max_budget_score: Optional[int] = Query(None, description="Maximum budget score filter"),
    limit: int = Query(10, description="Number of recommendations to return"),
    offset: int = Query(0, description="Number of recommendations to skip"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """Get AI recommendations for the current user with optional filters"""
    print(f"Fetching AI recommendations for user: {user.email}")
    
    try:
        # Start with user's recommendations
        query = db.query(models.AIRecommendation).filter(
            models.AIRecommendation.user_id == user.id
        )

        
        # Apply filters if provided
        if category:
            query = query.filter(models.AIRecommendation.category.ilike(f"%{category}%"))
        
        if location:
            query = query.filter(models.AIRecommendation.location.ilike(f"%{location}%"))
        
        if destination_type:
            query = query.filter(models.AIRecommendation.destination_type == destination_type)
        
        if min_rating is not None:
            query = query.filter(models.AIRecommendation.rating >= min_rating)
        
        if max_budget_score is not None:
            query = query.filter(models.AIRecommendation.budget_score <= max_budget_score)
        
        # Order by rating and popularity (most popular first)
        query = query.order_by(
            models.AIRecommendation.rating.desc(),
            models.AIRecommendation.popularity.desc(),
            models.AIRecommendation.created_at.desc()
        )
        
        # Apply pagination
        recommendations = query.offset(offset).limit(limit).all()
        
        print(f"Found {len(recommendations)} recommendations")
        return recommendations
        
    except Exception as e:
        print(f"Error fetching recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch recommendations: {str(e)}")


@router.get("/ai-recommendations/{recommendation_id}", response_model=schemas.AIRecommendationOut)
def get_ai_recommendation_by_id(
    recommendation_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """Get a specific AI recommendation by ID (only user's own recommendations)"""
    print(f"Fetching recommendation {recommendation_id} for user: {user.email}")
    
    try:
        recommendation = db.query(models.AIRecommendation).filter(
            and_(
                models.AIRecommendation.id == recommendation_id,
                models.AIRecommendation.user_id == user.id
            )
        ).first()
        
        if not recommendation:
            raise HTTPException(
                status_code=404, 
                detail="Recommendation not found or not accessible"
            )
        
        return recommendation
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch recommendation: {str(e)}")


  




@router.put("/ai-recommendations/{recommendation_id}", response_model=schemas.AIRecommendationOut)
def update_ai_recommendation(
    recommendation_id: int,
    payload: schemas.AIRecommendationUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)

):
    """Update an AI recommendation (only user's own recommendations)"""
    print(f"Updating recommendation {recommendation_id} for user: {user.email}")
    
    try:
        recommendation = db.query(models.AIRecommendation).filter(
            and_(
                models.AIRecommendation.id == recommendation_id,
                models.AIRecommendation.user_id == user.id
            )
        ).first()
        
        if not recommendation:
            raise HTTPException(
                status_code=404, 
                detail="Recommendation not found or not accessible"
            )
        
        # Update only provided fields
        for field, value in payload.dict(exclude_unset=True).items():
            setattr(recommendation, field, value)
        
        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)
        
        print(f"Recommendation updated successfully")
        return recommendation
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating recommendation: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update recommendation: {str(e)}")

@router.delete("/ai-recommendations/{recommendation_id}")
def delete_ai_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """Delete an AI recommendation (only user's own recommendations)"""
    print(f"Deleting recommendation {recommendation_id} for user: {user.email}")
    
    try:
        recommendation = db.query(models.AIRecommendation).filter(
            and_(
                models.AIRecommendation.id == recommendation_id,
                models.AIRecommendation.user_id == user.id
            )
        ).first()
        
        if not recommendation:
            raise HTTPException(
                status_code=404, 
                detail="Recommendation not found or not accessible"
            )
        
        db.delete(recommendation)
        db.commit()
        
        print(f"Recommendation deleted successfully")
        return {"message": "Recommendation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting recommendation: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete recommendation: {str(e)}")

# Bulk operations
@router.get("/ai-recommendations/by-type/{rec_type}", response_model=List[schemas.AIRecommendationOut])
def get_recommendations_by_type(
    rec_type: str,
    limit: int = Query(10),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """Get user's recommendations filtered by type"""
    print(f"Fetching {rec_type} recommendations for user: {user.email}")
    
    try:
        recommendations = db.query(models.AIRecommendation).filter(
            and_(
                models.AIRecommendation.user_id == user.id,
                models.AIRecommendation.type == rec_type
            )
        ).order_by(
            models.AIRecommendation.rating.desc()
        ).offset(offset).limit(limit).all()
        
        print(f"Found {len(recommendations)} {rec_type} recommendations")
        return recommendations
        
    except Exception as e:
        print(f"Error fetching recommendations by type: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch recommendations: {str(e)}")



@router.get("/ai-recommendations/stats")
def get_user_recommendation_stats(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """Get statistics about user's recommendations"""
    try:
        total_count = db.query(models.AIRecommendation).filter(
            models.AIRecommendation.user_id == user.id
        ).count()
        
        type_counts = db.query(
            models.AIRecommendation.type,
            db.func.count(models.AIRecommendation.id).label('count')
        ).filter(
            models.AIRecommendation.user_id == user.id
        ).group_by(models.AIRecommendation.type).all()
        
        avg_rating = db.query(
            db.func.avg(models.AIRecommendation.rating)
        ).filter(
            models.AIRecommendation.user_id == user.id
        ).scalar() or 0.0
        
        return {
            "total_recommendations": total_count,
            "by_type": {type_name: count for type_name, count in type_counts},
            "average_rating": round(avg_rating, 2)
        }
        
    except Exception as e:
        print(f"Error getting recommendation stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
        
        

@router.post("/ai-recommendations-debug")
def create_ai_recommendation_debug(
    payload: schemas.AIRecommendationCreate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Debug version with manual auth handling"""
    print(f"Debug endpoint called")
    print(f"Authorization header: {authorization}")
    print(f"Payload: {payload.dict()}")
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Get user manually
        user = get_current_user(token, db)
        print(f"User found: {user.email}")
        
        # Create recommendation
        recommendation = models.AIRecommendation(
            user_id=user.id,
            category=payload.category,
            location=payload.location,
            name=payload.name,
            type=payload.type,
            title=payload.title,
            description=payload.description,
            image=payload.image,
            tags=payload.tags,
            popularity=payload.popularity,
            rating=payload.rating,
            budget_score=payload.budget_score
        )
        
        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)
        
        return recommendation
        
    except Exception as e:
        print(f"Debug error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")
                