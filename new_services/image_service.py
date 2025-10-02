# services/image_service.py
import httpx
import asyncio
from typing import List, Dict, Optional
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        self.unsplash_headers = {"Authorization": f"Client-ID {settings.UNSPLASH_ACCESS_KEY}"}
        self.pexels_headers = {"Authorization": settings.PEXELS_API_KEY}
        self.timeout = 10
    
    async def get_images_for_recommendation(self, recommendation: Dict, image_count: int = 4) -> Dict:
        """
        Get images for a recommendation and update the recommendation object
        
        Args:
            recommendation: The recommendation dict to enhance
            image_count: Number of images to fetch
            
        Returns:
            Updated recommendation with image URLs
        """
        
        search_query = f"{recommendation.get('name', '')} {recommendation.get('location', '')} travel"
        images = await self.get_destination_images(search_query.strip(), image_count)
        
        # Update recommendation with image URLs for database
        if images:
            recommendation["image"] = images[0]["url"] if len(images) > 0 else None
            recommendation["image2"] = images[1]["url"] if len(images) > 1 else None
            recommendation["image3"] = images[2]["url"] if len(images) > 2 else None  
            recommendation["image4"] = images[3]["url"] if len(images) > 3 else None
        
        logger.info(f"Added {len(images)} images for trip recommendation: {recommendation.get('title', 'Unknown')}")
        return recommendation
    
    async def get_destination_images(self, search_query: str, count: int = 3) -> List[Dict]:
        """
        Get images from Unsplash first, then Pexels as fallback
        
        Args:
            search_query: Search query for images
            count: Number of images to fetch
            
        Returns:
            List of image dictionaries with urls and metadata
        """
        
        if not search_query.strip():
            return []
        
        # Try Unsplash first
        images = await self._get_unsplash_images(search_query, count)
        if images:
            return images
        
        # Fallback to Pexels
        images = await self._get_pexels_images(search_query, count)
        if images:
            return images
        
        # Return empty list if both fail
        logger.warning(f"No images found for query: {search_query}")
        return []
    
    async def _get_unsplash_images(self, query: str, count: int) -> List[Dict]:
        """Get images from Unsplash API"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.unsplash.com/search/photos",
                    headers=self.unsplash_headers,
                    params={
                        "query": query,
                        "per_page": min(count, 30),  # Unsplash max is 30
                        "orientation": "landscape",
                        "content_filter": "high",
                        "order_by": "relevant"
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    images = []
                    
                    for photo in data.get("results", []):
                        images.append({
                            "url": photo["urls"]["regular"],
                            "thumb_url": photo["urls"]["thumb"],
                            "alt": photo.get("alt_description", query),
                            "credit": photo["user"]["name"],
                            "source": "unsplash",
                            "width": photo.get("width", 0),
                            "height": photo.get("height", 0)
                        })
                    
                    logger.info(f"Unsplash: Found {len(images)} images for '{query}'")
                    return images[:count]
                    
                elif response.status_code == 403:
                    logger.warning("Unsplash API rate limit exceeded")
                else:
                    logger.warning(f"Unsplash API error: {response.status_code}")
                    
        except asyncio.TimeoutError:
            logger.warning("Unsplash API timeout")
        except Exception as e:
            logger.warning(f"Unsplash API error: {e}")
        
        return []
    
    async def _get_pexels_images(self, query: str, count: int) -> List[Dict]:
        """Get images from Pexels API"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.pexels.com/v1/search",
                    headers=self.pexels_headers,
                    params={
                        "query": query,
                        "per_page": min(count, 80),  # Pexels max is 80
                        "orientation": "landscape",
                        "size": "large"
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    images = []
                    
                    for photo in data.get("photos", []):
                        images.append({
                            "url": photo["src"]["large"],
                            "thumb_url": photo["src"]["medium"],
                            "alt": f"{query} - Photo by {photo['photographer']}",
                            "credit": photo["photographer"],
                            "source": "pexels",
                            "width": photo.get("width", 0),
                            "height": photo.get("height", 0)
                        })
                    
                    logger.info(f"Pexels: Found {len(images)} images for '{query}'")
                    return images[:count]
                    
                elif response.status_code == 429:
                    logger.warning("Pexels API rate limit exceeded")
                else:
                    logger.warning(f"Pexels API error: {response.status_code}")
                    
        except asyncio.TimeoutError:
            logger.warning("Pexels API timeout")
        except Exception as e:
            logger.warning(f"Pexels API error: {e}")
        
        return []

