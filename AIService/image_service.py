# services/image_service.py
import httpx
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
from core.config import settings
import json 

logger = logging.getLogger(__name__)

class ImageService:
    """
    Service for fetching images from Unsplash and Pexels APIs
    
    Features:
    - Batch processing to minimize API calls
    - Fallback mechanism (Unsplash -> Pexels -> Placeholder)
    - Rate limit handling
    - Caching support
    """
    
    def __init__(self):
        self.unsplash_headers = {
            "Authorization": f"Client-ID {settings.UNSPLASH_ACCESS_KEY}"
        } if hasattr(settings, 'UNSPLASH_ACCESS_KEY') and settings.UNSPLASH_ACCESS_KEY else None
        
        self.pexels_headers = {
            "Authorization": settings.PEXELS_API_KEY
        } if hasattr(settings, 'PEXELS_API_KEY') and settings.PEXELS_API_KEY else None
        
        self.timeout = 10
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 86400  # 24 hours for images
    
    # ========== MAIN PUBLIC METHODS ==========
    
    async def enhance_destinations_with_images(
        self, 
        recommendations: List[Dict],
        images_per_destination: int = 4
    ) -> List[Dict]:
        """
        Enhance destination recommendations with images (BATCH PROCESSING)
        
        This is for general destination recommendations where each destination
        needs multiple images (image, image2, image3, image4)
        
        Args:
            recommendations: List of destination recommendation dicts
            images_per_destination: Number of images to fetch per destination (default 4)
            
        Returns:
            Enhanced recommendations with image URLs populated
        """
        
        logger.info(f"Enhancing {len(recommendations)} destinations with images")
        
        if not recommendations:
            return recommendations
        
        # Extract search queries from all recommendations
        search_queries = [
            self._build_destination_search_query(rec) 
            for rec in recommendations
        ]
        
        # Batch fetch all images concurrently
        all_images = await self._batch_fetch_images(
            search_queries, 
            images_per_destination
        )
        
        # Attach images to each recommendation
        for i, rec in enumerate(recommendations):
            images = all_images[i] if i < len(all_images) else []
            
            # Populate image fields for database
            rec["image"] = images[0] if len(images) > 0 else None
            rec["image2"] = images[1] if len(images) > 1 else None
            rec["image3"] = images[2] if len(images) > 2 else None
            rec["image4"] = images[3] if len(images) > 3 else None
            
            logger.debug(f"Added {len(images)} images to {rec.get('title', 'Unknown')}")
        
        logger.info(f"Successfully enhanced all destinations with images")
        return recommendations
    
    async def enhance_trip_activities_with_images(
        self, 
        activities: List[Dict],
        images_per_activity: int = 2
    ) -> List[Dict]:
        """
        Enhance current trip activity recommendations with images (BATCH PROCESSING)
        
        This is for trip activities where each activity needs fewer images
        (coverImage and images array)
        
        Args:
            activities: List of activity recommendation dicts
            images_per_activity: Number of images per activity (default 2)
            
        Returns:
            Enhanced activities with images array and coverImage populated
        """
        
        logger.info(f"Enhancing {len(activities)} activities with images")
        
        if not activities:
            return activities
        
        # Extract search queries from all activities
        search_queries = [
            self._build_activity_search_query(activity) 
            for activity in activities
        ]
        
        # Batch fetch all images concurrently
        all_images = await self._batch_fetch_images(
            search_queries, 
            images_per_activity
        )
        
        # Attach images to each activity
        for i, activity in enumerate(activities):
            images = all_images[i] if i < len(all_images) else []
            
            # Populate images array and coverImage for frontend
            activity["images"] = images
            activity["coverImage"] = images[0] if images else None
            
            logger.debug(f"Added {len(images)} images to {activity.get('title', 'Unknown')}")
        
        logger.info(f"Successfully enhanced all activities with images")
        return activities
    
    # ========== BATCH PROCESSING ==========
    
    async def _batch_fetch_images(
        self, 
        search_queries: List[str], 
        images_per_query: int
    ) -> List[List[str]]:
        """
        Fetch images for multiple queries concurrently (EFFICIENT!)
        
        Instead of making 10 sequential API calls, we make them all at once.
        This is much faster and more efficient.
        
        Args:
            search_queries: List of search strings
            images_per_query: Number of images to fetch per query
            
        Returns:
            List of image URL lists, one per query
        """
        
        logger.info(f"Batch fetching images for {len(search_queries)} queries")
        
        # Create concurrent tasks for all queries
        tasks = [
            self._fetch_images_for_query(query, images_per_query)
            for query in search_queries
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any errors in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching images for query {i}: {result}")
                processed_results.append([])  # Empty list on error
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _fetch_images_for_query(
        self, 
        search_query: str, 
        count: int
    ) -> List[str]:
        """
        Fetch images for a single search query with caching and fallback
        
        Flow: Cache -> Unsplash -> Pexels -> Placeholder
        
        Args:
            search_query: What to search for
            count: How many images to return
            
        Returns:
            List of image URLs
        """
        
        # Check cache first
        cache_key = f"images_{search_query}_{count}"
        cached_images = self._get_from_cache(cache_key)
        if cached_images:
            logger.debug(f"Cache hit for: {search_query}")
            return cached_images
        
        # Try Unsplash first
        if self.unsplash_headers:
            images = await self._fetch_from_unsplash(search_query, count)
            if images:
                self._save_to_cache(cache_key, images)
                return images
        
        # Fallback to Pexels
        if self.pexels_headers:
            images = await self._fetch_from_pexels(search_query, count)
            if images:
                self._save_to_cache(cache_key, images)
                return images
        
        # Final fallback: placeholder images
        logger.warning(f"No images found for '{search_query}', using placeholders")
        return self._generate_placeholder_images(search_query, count)
    
    # ========== UNSPLASH API ==========
    
    async def _fetch_from_unsplash(self, query: str, count: int) -> List[str]:
        """
        Fetch images from Unsplash API
        
        Unsplash provides high-quality travel photography
        Rate limit: 50 requests/hour on free tier
        """
        
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
                    images = [
                        photo["urls"]["regular"]  # Good quality, not too large
                        for photo in data.get("results", [])
                    ]
                    
                    logger.info(f"Unsplash: Found {len(images)} images for '{query}'")
                    return images[:count]
                
                elif response.status_code == 403:
                    logger.warning("Unsplash API rate limit exceeded")
                elif response.status_code == 401:
                    logger.error("Unsplash API key invalid")
                else:
                    logger.warning(f"Unsplash API error: {response.status_code}")
                
        except asyncio.TimeoutError:
            logger.warning(f"Unsplash API timeout for query: {query}")
        except Exception as e:
            logger.error(f"Unsplash API error: {e}")
        
        return []
    
    # ========== PEXELS API ==========
    
    async def _fetch_from_pexels(self, query: str, count: int) -> List[str]:
        """
        Fetch images from Pexels API (fallback)
        
        Pexels is a good backup with more generous rate limits
        Rate limit: 200 requests/hour on free tier
        """
        
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
                    images = [
                        photo["src"]["large"]
                        for photo in data.get("photos", [])
                    ]
                    
                    logger.info(f"Pexels: Found {len(images)} images for '{query}'")
                    return images[:count]
                
                elif response.status_code == 429:
                    logger.warning("Pexels API rate limit exceeded")
                elif response.status_code == 401:
                    logger.error("Pexels API key invalid")
                else:
                    logger.warning(f"Pexels API error: {response.status_code}")
                
        except asyncio.TimeoutError:
            logger.warning(f"Pexels API timeout for query: {query}")
        except Exception as e:
            logger.error(f"Pexels API error: {e}")
        
        return []
    
    # ========== SEARCH QUERY BUILDERS ==========
    
    def _build_destination_search_query(self, recommendation: Dict) -> str:
        """
        Build optimal search query for destination recommendation
        
        Examples:
        - "Paris France travel"
        - "Tokyo Japan cityscape"
        - "Bali Indonesia beach"
        """
        
        name = recommendation.get("name", "")
        location = recommendation.get("location", "")
        settlement_type = recommendation.get("settlement_type", "city")
        
        # Build query with relevant keywords
        query_parts = [name, location]
        
        # Add context based on settlement type
        if settlement_type == "beach" or settlement_type == "island":
            query_parts.append("beach")
        elif settlement_type == "resort":
            query_parts.append("resort")
        else:
            query_parts.append("travel")
        
        return " ".join(filter(None, query_parts))
    
    def _build_activity_search_query(self, activity: Dict) -> str:
        """
        Build optimal search query for trip activity
        
        Examples:
        - "Eiffel Tower Paris"
        - "local market Barcelona"
        - "sushi restaurant Tokyo"
        """
        
        title = activity.get("title", "")
        destination = activity.get("destination", "")
        category = activity.get("category", "")
        
        # For specific attractions, use title + destination
        if category in ["Sightseeing", "Culture", "Nature"]:
            return f"{title} {destination}"
        
        # For general activities, use title only
        return title
    
    # ========== PLACEHOLDER GENERATION ==========
    
    def _generate_placeholder_images(self, query: str, count: int) -> List[str]:
        """
        Generate placeholder image URLs when real images aren't available
        
        Uses placeholder.com service with descriptive text
        """
        
        # Clean query for URL
        clean_query = query.replace(" ", "+")
        
        placeholders = []
        for i in range(count):
            url = f"https://via.placeholder.com/800x600/3B82F6/FFFFFF?text={clean_query}"
            placeholders.append(url)
        
        return placeholders
    
    # ========== CACHING ==========
    
    def _get_from_cache(self, key: str) -> Optional[List[str]]:
        """Get images from cache if not expired"""
        
        if key in self.cache:
            images, timestamp = self.cache[key]
            
            # Check if cache is still valid
            age = datetime.now().timestamp() - timestamp
            if age < self.cache_ttl:
                return images
            else:
                # Remove expired entry
                del self.cache[key]
        
        return None
    
    def _save_to_cache(self, key: str, images: List[str]) -> None:
        """Save images to cache with timestamp"""
        
        self.cache[key] = (images, datetime.now().timestamp())
        
        # Simple cache cleanup when it gets too large
        if len(self.cache) > 500:
            # Remove oldest 100 entries
            sorted_items = sorted(
                self.cache.items(), 
                key=lambda x: x[1][1]  # Sort by timestamp
            )
            for old_key, _ in sorted_items[:100]:
                del self.cache[old_key]
    
    # ========== UTILITY METHODS ==========
    
    def clear_cache(self):
        """Clear all cached images"""
        self.cache.clear()
        logger.info("Image cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics for monitoring"""
        return {
            "total_entries": len(self.cache),
            "cache_ttl_hours": self.cache_ttl / 3600
        }


# ========== STANDALONE TEST FUNCTIONS ==========

async def test_image_service():
    """
    Test the image service independently before integrating with AI service
    """
    
    print("Testing Image Service")
    print("=" * 50)
    
    # Initialize service
    image_service = ImageService()
    
    # Test 1: Single destination with 4 images
    print("\n1. Testing single destination (4 images):")
    destinations = [
        {
            "name": "Paris",
            "location": "France",
            "title": "Paris, France",
            "settlement_type": "city"
        }
    ]
    
    enhanced = await image_service.enhance_destinations_with_images(destinations, 4)
    print(f"   Images fetched: {bool(enhanced[0].get('image'))}")
    print(f"   Image 1: {enhanced[0].get('image', 'None')[:50]}...")
    print(f"   Image 2: {enhanced[0].get('image2', 'None')[:50]}...")
    
    # Test 2: Multiple destinations (batch processing)
    print("\n2. Testing batch processing (5 destinations):")
    destinations = [
        {"name": "Tokyo", "location": "Japan", "title": "Tokyo, Japan", "settlement_type": "city"},
        {"name": "Bali", "location": "Indonesia", "title": "Bali, Indonesia", "settlement_type": "island"},
        {"name": "Barcelona", "location": "Spain", "title": "Barcelona, Spain", "settlement_type": "city"},
        {"name": "Dubai", "location": "UAE", "title": "Dubai, UAE", "settlement_type": "city"},
        {"name": "Santorini", "location": "Greece", "title": "Santorini, Greece", "settlement_type": "island"}
    ]
    
    import time
    start = time.time()
    enhanced = await image_service.enhance_destinations_with_images(destinations, 4)
    elapsed = time.time() - start
    
    print(f"   Processed {len(enhanced)} destinations in {elapsed:.2f} seconds")
    print(f"   Average: {elapsed/len(enhanced):.2f} seconds per destination")
    
    # Test 3: Trip activities
    print("\n3. Testing trip activities (3 activities):")
    activities = [
        {"title": "Eiffel Tower", "destination": "Paris, France", "category": "Sightseeing"},
        {"title": "Local Market", "destination": "Paris, France", "category": "Culture"},
        {"title": "Seine River Cruise", "destination": "Paris, France", "category": "Activities"}
    ]
    
    enhanced = await image_service.enhance_trip_activities_with_images(activities, 2)
    print(f"   Activities enhanced: {len(enhanced)}")
    print(f"   First activity has {len(enhanced[0].get('images', []))} images")
    print(f"   Cover image: {enhanced[0].get('coverImage', 'None')[:50]}...")
    
    # Test 4: Cache performance
    print("\n4. Testing cache performance:")
    destinations = [{"name": "London", "location": "UK", "title": "London, UK", "settlement_type": "city"}]
    
    # First call
    start = time.time()
    await image_service.enhance_destinations_with_images(destinations, 4)
    first_call = time.time() - start
    
    # Second call (should be cached)
    start = time.time()
    await image_service.enhance_destinations_with_images(destinations, 4)
    second_call = time.time() - start
    
    print(f"   First call: {first_call:.3f} seconds")
    print(f"   Second call (cached): {second_call:.3f} seconds")
    print(f"   Speed improvement: {first_call/second_call:.1f}x faster")
    
    # Cache stats
    stats = image_service.get_cache_stats()
    print(f"   Cache entries: {stats['total_entries']}")
    
    print("\n" + "=" * 50)
    print("Image Service Test Complete!")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_image_service())
    
    
image_service = ImageService() 