# routes/avatar.py
import os
import time
import glob
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from auth.auth import get_current_user  # Import your auth function
from typing import Annotated
from deps import get_current_user, get_db  # Assuming you have get_db dependency
import models 

router = APIRouter()

UPLOAD_DIR= "uploads/avatars"
BASE_AVATAR_URL = "/static/avatars"  

def delete_existing_avatar(user_id: int, username: str):
    """
    Delete existing avatar files for the user.
    Searches for files matching the user's pattern and removes them.
    """
    try:
        # Pattern to match existing avatar files for this user
        # Format: username_* or userid_*
        patterns = [
            f"{username}_*.*",
            f"user_{user_id}_*.*",
            f"{user_id}_*.*"
        ]
        
        deleted_files = []
        for pattern in patterns:
            matching_files = glob.glob(os.path.join(UPLOAD_DIR, pattern))
            for file_path in matching_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_files.append(file_path)
        
        return deleted_files
    except Exception as e:
        print(f"Error deleting existing avatar: {e}")
        return []


def generate_avatar_filename(user_id: int, username: str, extension: str) -> str:
    """
    Generate a unique, identifiable filename for the user's avatar.
    Format: user_{user_id}_{timestamp}{extension}
    This ensures each user has a unique identifier.
    """
    timestamp = int(time.time())
    # Use user_id as primary identifier for uniqueness
    return f"user_{user_id}_{timestamp}{extension}"


def update_user_avatar_url(db: Session, user: models.User, avatar_filename: str) -> None:
    """
    Update the user's avatar_url in the database.
    """
    try:
        # Generate the public URL for the avatar
        avatar_url = f"{BASE_AVATAR_URL}/{avatar_filename}"
        
        # Update user's avatar_url field
        user.avatar_url = avatar_url
        db.commit()
        db.refresh(user)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user avatar URL: {str(e)}"
        )


@router.post("/user/upload-avatar")
async def upload_avatar(
    file: Annotated[UploadFile, File(...)],
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload user avatar with automatic deletion of existing avatar
    and database URL update.
    """
    # File size limit (5 MB)
    contents = await file.read()
    file_size = len(contents)
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 5MB limit."
        )

    # Allowed file extensions
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, JPEG, PNG, and WebP files are allowed."
        )

    try:
        # Delete existing avatar files for this user
        username = current_user.email.split('@')[0] if current_user.email else f"user_{current_user.id}"
        deleted_files = delete_existing_avatar(current_user.id, username)
        
        # Generate unique filename with user ID for perfect identification
        new_filename = generate_avatar_filename(current_user.id, username, ext)
        file_path = os.path.join(UPLOAD_DIR, new_filename)

        # Save the new avatar file
        with open(file_path, "wb") as f:
            f.write(contents)

        # Update user's avatar_url in database
        update_user_avatar_url(db, current_user, new_filename)

        return {
            "message": "Avatar uploaded successfully!",
            "filename": new_filename,
            "avatar_url": current_user.avatar_url,
            "user_id": current_user.id,
            "deleted_files": len(deleted_files),
            "file_path": file_path
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload avatar: {str(e)}"
        )


@router.get("/user/avatar")
async def get_user_avatar(
    current_user: models.User = Depends(get_current_user)
):
    """
    Get current user's avatar URL.
    Returns the avatar_url that can be used directly in frontend.
    """
    return {
        "user_id": current_user.id,
        "avatar_url": current_user.avatar_url,
        "has_avatar": bool(current_user.avatar_url)
    }


@router.get("/user/{user_id}/avatar")
async def get_user_avatar_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get any user's avatar URL by user ID.
    Useful for displaying other users' avatars.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "user_id": user.id,
        "avatar_url": user.avatar_url,
        "has_avatar": bool(user.avatar_url)
    }


@router.delete("/user/avatar")
async def delete_user_avatar(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete user's current avatar and remove from database.
    """
    if not current_user.avatar_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No avatar to delete"
        )
    
    try:
        # Delete physical files
        username = current_user.email.split('@')[0] if current_user.email else f"user_{current_user.id}"
        deleted_files = delete_existing_avatar(current_user.id, username)
        
        # Clear avatar_url in database
        current_user.avatar_url = None
        db.commit()
        db.refresh(current_user)
             
        return {
            "message": "Avatar deleted successfully",
            "deleted_files": len(deleted_files)
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete avatar: {str(e)}"
        )


# Static file serving endpoint (add this to your main app or separate static handler)
@router.get("/static/avatars/{filename}")
async def serve_avatar(filename: str):
    """
    Serve avatar files statically.
    This endpoint makes user.avatar_url directly accessible.
    """
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    return FileResponse(
        file_path,
        media_type="image/jpeg",  # Will be auto-detected by FastAPI
        headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
    )